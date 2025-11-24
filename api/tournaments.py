from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime
from models.tournament import Tournament

tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')


@tournaments_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить список всех турниров',
    'description': 'Возвращает список турниров с возможностью фильтрации по статусу',
    'parameters': [
        {
            'name': 'status',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Статус турнира для фильтрации',
            'enum': ['DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED']
        }
    ],
    'responses': {
        200: {
            'description': 'Список турниров получен успешно',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'start_date': {'type': 'string', 'format': 'date'},
                        'end_date': {'type': 'string', 'format': 'date'},
                        'venue': {'type': 'string'},
                        'city': {'type': 'string'},
                        'country': {'type': 'string'},
                        'status': {'type': 'string'},
                        'tatami_count': {'type': 'integer'},
                        'athletes_count': {'type': 'integer'},
                        'progress_percentage': {'type': 'integer'}
                    }
                }
            }
        }
    }
})
def get_tournaments():
    """Получить список всех турниров"""
    try:
        status = request.args.get('status')

        query = Tournament.query
        if status:
            query = query.filter_by(status=status)

        tournaments = query.order_by(Tournament.start_date.desc()).all()

        result = []
        for tournament in tournaments:
            result.append({
                'id': tournament.id,
                'name': tournament.name,
                'description': tournament.description,
                'start_date': tournament.start_date.isoformat() if tournament.start_date else None,
                'end_date': tournament.end_date.isoformat() if tournament.end_date else None,
                'venue': tournament.venue,
                'city': tournament.city,
                'country': tournament.country,
                'status': tournament.status,
                'tatami_count': tournament.tatami_count,
                'athletes_count': tournament.athletes_count,
                'progress_percentage': tournament.progress_percentage
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении турниров: {str(e)}'
        }), 500


@tournaments_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Создать новый турнир',
    'description': 'Создает новый турнир в системе',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name', 'start_date', 'end_date'],
                'properties': {
                    'name': {'type': 'string', 'description': 'Название турнира'},
                    'description': {'type': 'string', 'description': 'Описание турнира'},
                    'start_date': {'type': 'string', 'format': 'date', 'description': 'Дата начала (ISO формат)'},
                    'end_date': {'type': 'string', 'format': 'date', 'description': 'Дата окончания (ISO формат)'},
                    'venue': {'type': 'string', 'description': 'Место проведения'},
                    'city': {'type': 'string', 'description': 'Город'},
                    'country': {'type': 'string', 'description': 'Страна', 'default': 'Россия'},
                    'tatami_count': {'type': 'integer', 'description': 'Количество татами', 'default': 1}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Турнир успешно создан',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'start_date': {'type': 'string'},
                    'end_date': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def create_tournament():
    """Создать новый турнир"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('name') or not data.get('start_date') or not data.get('end_date'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: name, start_date, end_date'
            }), 400

        tournament = Tournament(
            name=data['name'],
            description=data.get('description'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            venue=data.get('venue'),
            city=data.get('city'),
            country=data.get('country', 'Россия'),
            tatami_count=data.get('tatami_count', 1)
        )

        if tournament.save_to_db():
            return jsonify({
                'id': tournament.id,
                'name': tournament.name,
                'start_date': tournament.start_date.isoformat(),
                'end_date': tournament.end_date.isoformat(),
                'status': tournament.status
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при создании турнира'
            }), 400

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Неверный формат даты: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании турнира: {str(e)}'
        }), 500


@tournaments_bp.route('/<int:tournament_id>', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить информацию о турнире',
    'description': 'Возвращает детальную информацию о конкретном турнире',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID турнира'
        }
    ],
    'responses': {
        200: {
            'description': 'Информация о турнире',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'start_date': {'type': 'string'},
                    'end_date': {'type': 'string'},
                    'venue': {'type': 'string'},
                    'city': {'type': 'string'},
                    'country': {'type': 'string'},
                    'status': {'type': 'string'},
                    'tatami_count': {'type': 'integer'},
                    'athletes_count': {'type': 'integer'},
                    'progress_percentage': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Турнир не найден'
        }
    }
})
def get_tournament(tournament_id):
    """Получить информацию о турнире"""
    try:
        tournament = Tournament.query.get(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        return jsonify({
            'id': tournament.id,
            'name': tournament.name,
            'description': tournament.description,
            'start_date': tournament.start_date.isoformat() if tournament.start_date else None,
            'end_date': tournament.end_date.isoformat() if tournament.end_date else None,
            'venue': tournament.venue,
            'city': tournament.city,
            'country': tournament.country,
            'status': tournament.status,
            'tatami_count': tournament.tatami_count,
            'athletes_count': tournament.athletes_count,
            'progress_percentage': tournament.progress_percentage
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении турнира: {str(e)}'
        }), 500


@tournaments_bp.route('/<int:tournament_id>', methods=['PUT'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Обновить информацию о турнире',
    'description': 'Обновляет данные турнира',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID турнира'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'start_date': {'type': 'string', 'format': 'date'},
                    'end_date': {'type': 'string', 'format': 'date'},
                    'venue': {'type': 'string'},
                    'city': {'type': 'string'},
                    'country': {'type': 'string'},
                    'status': {'type': 'string'},
                    'tatami_count': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Турнир успешно обновлен'
        },
        404: {
            'description': 'Турнир не найден'
        },
        400: {
            'description': 'Ошибка при обновлении'
        }
    }
})
def update_tournament(tournament_id):
    """Обновить информацию о турнире"""
    try:
        tournament = Tournament.query.get(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        # Обновляем поля
        for key, value in data.items():
            if hasattr(tournament, key):
                if key in ['start_date', 'end_date'] and isinstance(value, str):
                    value = datetime.fromisoformat(value)
                setattr(tournament, key, value)

        if tournament.save():
            return jsonify({
                'success': True,
                'message': 'Турнир успешно обновлен',
                'tournament': {
                    'id': tournament.id,
                    'name': tournament.name,
                    'status': tournament.status
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при обновлении турнира'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении турнира: {str(e)}'
        }), 500


@tournaments_bp.route('/<int:tournament_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Удалить турнир',
    'description': 'Удаляет турнир из системы',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID турнира'
        }
    ],
    'responses': {
        200: {
            'description': 'Турнир успешно удален'
        },
        404: {
            'description': 'Турнир не найден'
        },
        400: {
            'description': 'Ошибка при удалении'
        }
    }
})
def delete_tournament(tournament_id):
    """Удалить турнир"""
    try:
        tournament = Tournament.query.get(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        if tournament.delete():
            return jsonify({
                'success': True,
                'message': 'Турнир удален'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при удалении турнира'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении турнира: {str(e)}'
        }), 500


@tournaments_bp.route('/<int:tournament_id>/categories', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить категории турнира',
    'description': 'Возвращает список категорий конкретного турнира',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID турнира'
        }
    ],
    'responses': {
        200: {
            'description': 'Список категорий',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'gender': {'type': 'string'},
                        'min_weight': {'type': 'number'},
                        'max_weight': {'type': 'number'},
                        'min_age': {'type': 'integer'},
                        'max_age': {'type': 'integer'},
                        'athletes_count': {'type': 'integer'}
                    }
                }
            }
        },
        404: {
            'description': 'Турнир не найден'
        }
    }
})
def get_tournament_categories(tournament_id):
    """Получить категории турнира"""
    try:
        tournament = Tournament.query.get(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        result = []
        for category in tournament.categories:
            result.append({
                'id': category.id,
                'name': category.name,
                'gender': category.gender,
                'min_weight': category.min_weight,
                'max_weight': category.max_weight,
                'min_age': category.min_age,
                'max_age': category.max_age,
                'athletes_count': category.athletes_count
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении категорий: {str(e)}'
        }), 500