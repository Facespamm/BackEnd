from flask import Blueprint, request, jsonify
from flasgger import swag_from
from models.club import Club

clubs_bp = Blueprint('clubs', __name__, url_prefix='/clubs')


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
        clubs = Club.query.filter_by(is_active=True).order_by(Club.name).all()

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
def create_club():
    """Создать новый клуб"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Название клуба обязательно'
            }), 400

        club = Club(
            name=data['name'],
            short_name=data.get('short_name'),
            city=data.get('city'),
            country=data.get('country', 'Россия'),
            address=data.get('address'),
            phone=data.get('phone'),
            email=data.get('email'),
            website=data.get('website'),
            coach_name=data.get('coach_name'),
            founded_year=data.get('founded_year')
        )

        if club.save():
            return jsonify({
                'success': True,
                'message': 'Клуб успешно создан',
                'club_id': club.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении клуба'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании клуба: {str(e)}'
        }), 500