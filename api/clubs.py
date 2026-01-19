from flask import Blueprint, request, jsonify
from flasgger import swag_from

from repository.club_repo import ClubRepository

clubs_bp = Blueprint('clubs', __name__, url_prefix='/clubs')
club_repo = ClubRepository()

@clubs_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Clubs'],
    'summary': 'Получить список клубов',
    'description': 'Возвращает список всех активных клубов',
    'responses': {
        200: {
            'description': 'Список клубов получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'clubs': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'short_name': {'type': 'string'},
                                'city': {'type': 'string'},
                                'country': {'type': 'string'},
                                'coach_name': {'type': 'string'},
                                'athletes_count': {'type': 'integer'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
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
                'athletes_count': club.athletes_count
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
@swag_from({
    "tags": ["Clubs"],
    "summary": "Создать новый клуб",
    "description": "Добавляет новый спортивный клуб в систему",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string", "example": "Динамо"},
                    "short_name": {"type": "string", "example": "ДНМ"},
                    "city": {"type": "string", "example": "Москва"},
                    "country": {"type": "string", "example": "Россия"},
                    "coach_name": {"type": "string", "example": "Петров А.В."},
                    "address": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "website": {"type": "string"},
                    "founded_year": {"type": "integer", "example": 1923}
                }
            }
        }
    ],
    "responses": {
        201: {
            "description": "Клуб успешно создан",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "club_id": {"type": "integer"}
                }
            }
        },
        400: {"description": "Ошибка валидации или клуб уже существует"}
    }
})
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