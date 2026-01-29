from flask import Blueprint, request, jsonify
from flasgger import swag_from

from repository.athlete_repo import AthleteRepository
from repository.club_repo import ClubRepository

clubs_bp = Blueprint('clubs', __name__, url_prefix='/clubs')
club_repo = ClubRepository()

@clubs_bp.route('/', methods=['GET'])
def get_clubs():
    """Получить список клубов"""
    try:
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

@clubs_bp.route('/', methods=['POST'])
def create_club():
    """Создать новый клуб"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Не передан JSON"}), 400

        if not data.get('name'):
            return jsonify({"success": False, "message": "Название клуба обязательно"}), 400

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
@swag_from({
    "tags": ["Клубы"],
    "summary": "Удалить клуб по ID",
    "description": "Удаляет клуб. У спортсменов, привязанных к клубу, поле club_id становится NULL.",
    "parameters": [
        {
            "name": "club_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID клуба"
        }
    ],
    "responses": {
        200: {
            "description": "Клуб успешно удалён, спортсмены отвязаны",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"}
                }
            }
        },
        404: {"description": "Клуб не найден"},
        400: {"description": "Не удалось удалить клуб"},
        500: {"description": "Ошибка сервера"}
    }
})
def delete_club(club_id):
    """Удалить клуб по ID"""
    try:
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
@swag_from({
    "tags": ["Клубы"],
    "summary": "Обновить данные клуба",
    "description": "Обновляет поля клуба. Обновляются только переданные в запросе поля.",
    "parameters": [
        {
            "name": "club_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID клуба"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "short_name": {"type": "string"},
                    "city": {"type": "string"},
                    "country": {"type": "string"},
                    "address": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "website": {"type": "string"},
                    "coach_name": {"type": "string"},
                    "founded_year": {"type": "integer"}
                }
            }
        }
    ],
    "responses": {
        200: {
            "description": "Клуб успешно обновлён",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "club": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "short_name": {"type": "string"},
                            "city": {"type": "string"},
                            "country": {"type": "string"},
                            "address": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string"},
                            "website": {"type": "string"},
                            "coach_name": {"type": "string"},
                            "founded_year": {"type": "integer"}
                        }
                    }
                }
            }
        },
        404: {"description": "Клуб не найден"},
        400: {"description": "Некорректные данные или ничего не передано"},
        500: {"description": "Ошибка сервера"}
    }
})
def update_club(club_id):
    """Обновить данные клуба по ID"""
    try:
        club = club_repo.get_club_by_id(club_id)
        if not club:
            return jsonify({
                "success": False,
                "message": f"Клуб с ID {club_id} не найден"
            }), 404

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


@clubs_bp.route('/<club_id>/club-athletes', methods=['GET'])
def get_club_athletes(club_id):
    """Получить всех участников клуба"""
    try:
        # Получаем параметры
        # only_active = request.args.get('only_active', 'true').lower() == 'true'
        include_tournament_info = request.args.get('include_tournament_info', 'false').lower() == 'true'
        tournament_id = request.args.get('tournament_id')

        if not club_id:
            return jsonify({
                'success': False,
                'message': 'Не указан club_id'
            }), 400

        # Проверяем существование клуба
        club = club_repo.get_club_by_id(club_id)
        if not club:
            return jsonify({
                'success': False,
                'message': f'Клуб с ID {club_id} не найден'
            }), 404

        athlete_repo = AthleteRepository()
        athletes =  athlete_repo.get_athletes_by_club_id(club_id, tournament_id, include_tournament_info)

        # Формируем результат
        result = []
        for athlete in athletes:

            athlete_data = {
                'id': athlete.id,
                'user_id': athlete.user_id,
                'last_name': athlete.user.last_name,
                'first_name': athlete.user.first_name,
                'middle_name': athlete.user.middle_name,
                'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                'age': athlete.age,
                'gender': athlete.gender,
                'rank': athlete.rank.name if athlete.rank else None,
                'license_number': athlete.license_number,
                'medical_check': athlete.medical_check,
                'insurance_number': athlete.insurance_number,
                'is_active': athlete.is_active
            }

            # Добавляем информацию о турнирах
            if include_tournament_info:
                tournaments = []
                for tournament in athlete.registration.tournament_categories.tournament:
                    tournament_data = {
                        'tournament_id': tournament.id,
                        'tournament_name': tournament.name
                    }
                    tournaments.append(tournament_data)

                athlete_data['tournaments'] = tournaments

            result.append(athlete_data)

        return jsonify({
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