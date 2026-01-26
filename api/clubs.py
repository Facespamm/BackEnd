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