from flask import Blueprint, request, jsonify
from flasgger import swag_from
from models.weighing import Weighing
from models.tournament import Tournament
from models.athlete import Athlete

weighing_bp = Blueprint('weighing', __name__, url_prefix='/weighing')


@weighing_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Weighing'],
    'summary': 'Получить список взвешиваний',
    'description': 'Возвращает список взвешиваний с возможностью фильтрации',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'ID турнира для фильтрации'
        },
        {
            'name': 'athlete_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'ID спортсмена для фильтрации'
        }
    ],
    'responses': {
        200: {
            'description': 'Список взвешиваний получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'weighings': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'athlete_name': {'type': 'string'},
                                'weight': {'type': 'number'},
                                'weight_category': {'type': 'string'},
                                'tournament_name': {'type': 'string'},
                                'weighing_time': {'type': 'string', 'format': 'date-time'},
                                'status': {'type': 'string'},
                                'is_valid': {'type': 'boolean'}
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
def get_weighings():
    """Получить список взвешиваний"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        athlete_id = request.args.get('athlete_id', type=int)

        query = Weighing.query

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        if athlete_id:
            query = query.filter_by(athlete_id=athlete_id)

        weighings = query.order_by(Weighing.weighing_time.desc()).all()

        result = []
        for weighing in weighings:
            result.append({
                'id': weighing.id,
                'athlete_name': weighing.athlete.full_name if weighing.athlete else None,
                'weight': weighing.weight,
                'weight_category': weighing.weight_category,
                'tournament_name': weighing.tournament.name if weighing.tournament else None,
                'weighing_time': weighing.weighing_time.isoformat(),
                'status': weighing.status_display,
                'is_valid': weighing.is_valid
            })

        return jsonify({
            'success': True,
            'weighings': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении взвешиваний: {str(e)}'
        }), 500


@weighing_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Weighing'],
    'summary': 'Создать запись о взвешивании',
    'description': 'Создает новую запись о взвешивании спортсмена',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['tournament_id', 'athlete_id', 'weight'],
                'properties': {
                    'tournament_id': {
                        'type': 'integer',
                        'description': 'ID турнира'
                    },
                    'athlete_id': {
                        'type': 'integer',
                        'description': 'ID спортсмена'
                    },
                    'weight': {
                        'type': 'number',
                        'format': 'float',
                        'description': 'Вес спортсмена в кг'
                    },
                    'notes': {
                        'type': 'string',
                        'description': 'Дополнительные заметки'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Взвешивание успешно записано',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'weighing_id': {'type': 'integer'},
                    'weight_category': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Турнир или спортсмен не найден'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def create_weighing():
    """Создать запись о взвешивании"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('tournament_id') or not data.get('athlete_id') or not data.get('weight'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: tournament_id, athlete_id, weight'
            }), 400

        # Проверяем существование турнира и участника
        tournament = Tournament.query.get(data['tournament_id'])
        athlete = Athlete.query.get(data['athlete_id'])

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        if not athlete:
            return jsonify({
                'success': False,
                'message': 'Участник не найден'
            }), 404

        weighing = Weighing(
            tournament_id=data['tournament_id'],
            athlete_id=data['athlete_id'],
            weight=data['weight'],
            notes=data.get('notes')
        )

        # Определяем категорию
        weighing.determine_category()

        if weighing.save():
            return jsonify({
                'success': True,
                'message': 'Взвешивание успешно записано',
                'weighing_id': weighing.id,
                'weight_category': weighing.weight_category,
                'status': weighing.status_display
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении взвешивания'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании записи взвешивания: {str(e)}'
        }), 500