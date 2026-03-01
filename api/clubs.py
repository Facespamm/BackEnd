from flask import Blueprint, request, jsonify

from database.db import create_session
from repository.athlete_repo import AthleteRepository
from repository.club_repo import ClubRepository

clubs_bp = Blueprint('clubs', __name__, url_prefix='/api/clubs')

@clubs_bp.route('/', methods=['GET'])
def get_clubs():
    """Получить список клубов"""
    try:
        with create_session() as session:
            club_repo = ClubRepository(session)
            athlete_repo = AthleteRepository(session)

            clubs = club_repo.get_clubs()

            result = []
            for club in clubs:
                result.append({
                    'id': club.id,
                    'name': club.name,
                    'short_name': club.short_name,
                    'city': club.city,
                    'country': club.country,
                    'coach_name': club.coach_name,
                    'athletes_count':athlete_repo.count_athletes_in_club(club.id)
                })

        return jsonify({
            'success': True,
            'clubs': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении клубов: {str(e)}'
        }), 500


@clubs_bp.route('/search', methods=['GET'])
def search_athletes():
    """Поиск спортсменов по ФИО (частичное совпадение)"""
    try:
        # Параметры запроса: можно передать отдельно или один общий q
        last_name = request.args.get('last_name', '').strip()
        first_name = request.args.get('first_name', '').strip()
        middle_name = request.args.get('middle_name', '').strip()
        q = request.args.get('q', '').strip()  # альтернативно: "Иванов Иван Иванович"

        name_query = {}

        if q:
            # Если передан общий q — разбиваем на части (по пробелам)
            parts = q.split()
            if len(parts) >= 1:
                name_query['last_name'] = parts[0]
            if len(parts) >= 2:
                name_query['first_name'] = parts[1]
            if len(parts) >= 3:
                name_query['middle_name'] = ' '.join(parts[2:])
        else:
            # Отдельные параметры
            if last_name:
                name_query['last_name'] = last_name
            if first_name:
                name_query['first_name'] = first_name
            if middle_name:
                name_query['middle_name'] = middle_name

        if not name_query:
            return jsonify({
                'success': False,
                'message': 'Не переданы параметры поиска (last_name, first_name, middle_name или q)'
            }), 400

        # Поиск без ограничения по клубу (club_id=None)
        with AthleteRepository() as athlete_repo:
            athletes = athlete_repo.search_athletes_by_name(name_query=name_query, club_id=None)

            result = []
            for athlete in athletes:
                club_name = athlete.club.name if athlete.club else None
                club_short_name = athlete.club.short_name if athlete.club else None

                athlete_data = {
                    'id': athlete.id,
                    'user_id': athlete.user_id,
                    'last_name': athlete.user.last_name or 'Неизвестно',
                    'first_name': athlete.user.first_name or 'Неизвестно',
                    'middle_name': athlete.user.middle_name or None,
                    'full_name': ' '.join(filter(None, [
                        athlete.user.last_name or '',
                        athlete.user.first_name or '',
                        athlete.user.middle_name or ''
                    ])),
                    'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                    'age': athlete.age,
                    'gender': athlete.gender,
                    'rank': athlete.rank.level if athlete.rank else None,
                    'license_number': athlete.license_number,
                    'medical_check': athlete.medical_check,
                    'insurance_number': athlete.insurance_number,
                    'is_active': athlete.is_active,
                    'club': {
                        'id': athlete.club.id if athlete.club else None,
                        'name': club_name,
                        'short_name': club_short_name
                    } if athlete.club else None
                }
                result.append(athlete_data)

        return jsonify({
            'success': True,
            'search_params': name_query or {'q': q},
            'athletes_count': len(result),
            'athletes': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при поиске спортсменов: {str(e)}'
        }), 500


@clubs_bp.route('/', methods=['POST'])
def create_club():
    """Создать новый клуб"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Не передан JSON"}), 400

        if not data.get('name'):
            return jsonify({"success": False, "message": "Название клуба обязательно"}), 400

        with ClubRepository() as club_repo:
            existing_club = club_repo.get_club_by_name(data['name'].strip())

            if existing_club:
                return jsonify({"success": False, "message": "Клуб с таким названием уже существует"}), 400

            is_create = club_repo.create_club(data)

        if is_create:
            return jsonify({
                "success": True,
                "message": "Клуб успешно создан"
            }), 201
        else:
            return jsonify({"success": False, "message": "Ошибка при сохранении в базу"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": f"Ошибка сервера: {str(e)}"}), 500


@clubs_bp.route('/<int:club_id>', methods=['DELETE'])
def delete_club(club_id):
    """Удалить клуб по ID"""
    try:
        with ClubRepository() as club_repo:
            club = club_repo.get_club_by_id(club_id)
            if not club:
                return jsonify({
                    "success": False,
                    "message": f"Клуб с ID {club_id} не найден"
                }), 404

            # Проверка на наличие спортсменов УДАЛЕНА — теперь удаляем всегда

            is_deleted = club_repo.delete_club(club_id)

        if is_deleted:
            return jsonify({
                "success": True,
                "message": f"Клуб '{club.name}' успешно удалён, спортсмены отвязаны"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Не удалось удалить клуб"
            }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Ошибка при удалении клуба: {str(e)}"
        }), 500

@clubs_bp.route('/<int:club_id>', methods=['PUT'])
def update_club(club_id):
    """Обновить данные клуба по ID"""
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({
                "success": False,
                "message": "Не переданы данные для обновления"
            }), 400

        update_data = {}

        # Обработка каждого возможного поля
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({"success": False, "message": "Название клуба не может быть пустым"}), 400
            update_data['name'] = name

        if 'short_name' in data:
            update_data['short_name'] = data['short_name'].strip() if data['short_name'] else None

        if 'city' in data:
            update_data['city'] = data['city'].strip() if data['city'] else None

        if 'country' in data:
            update_data['country'] = data['country'].strip() if data['country'] else 'Россия'

        if 'address' in data:
            update_data['address'] = data['address'].strip() if data['address'] else None

        if 'phone' in data:
            update_data['phone'] = data['phone'].strip() if data['phone'] else None

        if 'email' in data:
            update_data['email'] = data['email'].strip() if data['email'] else None

        if 'website' in data:
            update_data['website'] = data['website'].strip() if data['website'] else None

        if 'coach_name' in data:
            update_data['coach_name'] = data['coach_name'].strip() if data['coach_name'] else None

        if 'founded_year' in data:
            try:
                update_data['founded_year'] = int(data['founded_year'])
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "message": "Поле founded_year должно быть целым числом"
                }), 400

        if not update_data:
            return jsonify({
                "success": False,
                "message": "Не передано ни одно поле для обновления"
            }), 400

        with ClubRepository() as club_repo:
            club = club_repo.get_club_by_id(club_id)
            if not club:
                return jsonify({
                    "success": False,
                    "message": f"Клуб с ID {club_id} не найден"
                }), 404

            is_updated = club_repo.update_club(club_id, update_data)

            if not is_updated:
                return jsonify({
                    "success": False,
                    "message": "Не удалось обновить данные клуба"
                }), 400

            # Получаем актуальные данные после обновления
            updated_club = club_repo.get_club_by_id(club_id)

        return jsonify({
            "success": True,
            "message": "Клуб успешно обновлён",
            "club": {
                "id": updated_club.id,
                "name": updated_club.name,
                "short_name": updated_club.short_name,
                "city": updated_club.city,
                "country": updated_club.country,
                "address": updated_club.address,
                "phone": updated_club.phone,
                "email": updated_club.email,
                "website": updated_club.website,
                "coach_name": updated_club.coach_name,
                "founded_year": updated_club.founded_year
            }
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Ошибка при обновлении клуба: {str(e)}"
        }), 500


@clubs_bp.route('/<int:club_id>/club-athletes/', methods=['GET'])
def get_club_athletes(club_id):
    """Получить всех участников клуба"""
    try:
        include_tournament_info = request.args.get('include_tournament_info', 'false').lower() == 'true'

        # tournament_id как int или None (пустой/не передан → None)
        tournament_id = request.args.get('tournament_id', type=int)

        # Проверяем клуб
        with create_session() as session:
            club_repo = ClubRepository(session)
            club = club_repo.get_club_by_id(club_id)
            if not club:
                return jsonify({
                    'success': False,
                    'message': f'Клуб с ID {club_id} не найден'
                }), 404

            athlete_repo = AthleteRepository(session)
            athletes = athlete_repo.get_athletes_by_club_id(
                club_id=club_id,
                tournament_id=tournament_id,
                include_tournament_info=include_tournament_info
            )

            result = []
            for athlete in athletes:
                athlete_data = {
                    'id': athlete.id,
                    'user_id': athlete.user_id,
                    'last_name': athlete.user.last_name or 'Неизвестно',
                    'first_name': athlete.user.first_name or 'Неизвестно',
                    'middle_name': athlete.user.middle_name or None,
                    'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                    'age': athlete.age,
                    'gender': athlete.gender,
                    # ← Главное исправление: rank теперь берём из поля level (или description)
                    # Если нужно описание — используйте athlete.rank.description
                    # Если нужно оба — f"{athlete.rank.level} {athlete.rank.description}"
                    'rank': athlete.rank.level if athlete.rank else None,
                    'license_number': athlete.license_number,
                    'medical_check': athlete.medical_check,
                    'insurance_number': athlete.insurance_number,
                    'is_active': athlete.is_active
                }

                if include_tournament_info:
                    tournaments = []
                    if (hasattr(athlete, 'registration') and
                            athlete.registration and
                            hasattr(athlete.registration, 'tournament_categories')):
                        for tc in athlete.registration.tournament_categories:
                            if hasattr(tc, 'tournament') and tc.tournament:
                                tournaments.append({
                                    'tournament_id': tc.tournament.id,
                                    'tournament_name': tc.tournament.name
                                })
                    athlete_data['tournaments'] = tournaments

                result.append(athlete_data)

        return jsonify({
            'success': True,
            'club_id': club.id,
            'club_name': club.name,
            'athletes_count': len(result),
            'athletes': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участников клуба: {str(e)}'
        }), 500