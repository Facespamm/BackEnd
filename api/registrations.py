from flask import Blueprint, request, jsonify
from flasgger import swag_from
from models.athlete import Athlete
from models.tournament import Tournament
from models.category import Category
from models.associations import category_athletes
from databse.db import db

registrations_bp = Blueprint('registrations', __name__, url_prefix='/registrations')


@registrations_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Registrations'],
    'summary': 'Зарегистрировать атлета на турнир',
    'description': 'Регистрирует атлета в конкретной категории турнира',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['athlete_id', 'tournament_id', 'category_id'],
                'properties': {
                    'athlete_id': {'type': 'integer', 'description': 'ID атлета'},
                    'tournament_id': {'type': 'integer', 'description': 'ID турнира'},
                    'category_id': {'type': 'integer', 'description': 'ID категории'},
                    'notes': {'type': 'string', 'description': 'Дополнительные заметки'}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Атлет успешно зарегистрирован',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'registration_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Атлет, турнир или категория не найдены'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def register_athlete():
    """Зарегистрировать атлета на турнир"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        required_fields = ['athlete_id', 'tournament_id', 'category_id']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            return jsonify({
                'success': False,
                'message': f'Обязательные поля: {", ".join(missing)}'
            }), 400

        # Проверяем существование записей
        athlete = Athlete.query.get(data['athlete_id'])
        tournament = Tournament.query.get(data['tournament_id'])
        category = Category.query.get(data['category_id'])

        if not athlete:
            return jsonify({
                'success': False,
                'message': 'Атлет не найден'
            }), 404

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        # Проверяем, что категория принадлежит турниру
        if category.tournament_id != tournament.id:
            return jsonify({
                'success': False,
                'message': 'Категория не принадлежит указанному турниру'
            }), 400

        # Проверяем, не зарегистрирован ли уже атлет в этой категории
        if athlete in category.athletes:
            return jsonify({
                'success': False,
                'message': 'Атлет уже зарегистрирован в этой категории'
            }), 400

        # Проверяем соответствие полу
        if athlete.gender != category.gender and category.gender not in ['MIXED', 'ANY']:
            return jsonify({
                'success': False,
                'message': f'Атлет не соответствует полу категории ({category.gender})'
            }), 400

        # Проверяем соответствие возрасту
        if category.min_age and athlete.age < category.min_age:
            return jsonify({
                'success': False,
                'message': f'Атлет слишком молод для категории (мин. возраст: {category.min_age})'
            }), 400

        if category.max_age and athlete.age > category.max_age:
            return jsonify({
                'success': False,
                'message': f'Атлет слишком стар для категории (макс. возраст: {category.max_age})'
            }), 400

        # Регистрируем атлета
        category.athletes.append(athlete)

        # Используем save_to_db вместо ручного commit
        if category.save_to_db():
            return jsonify({
                'success': True,
                'message': 'Атлет успешно зарегистрирован',
                'registration_id': f"{athlete.id}-{category.id}"  # Составной ID
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении регистрации'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при регистрации атлета: {str(e)}'
        }), 500


@registrations_bp.route('/tournament/<int:tournament_id>', methods=['GET'])
@swag_from({
    'tags': ['Registrations'],
    'summary': 'Получить список регистраций на турнир',
    'description': 'Возвращает список всех зарегистрированных атлетов на турнир',
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
            'description': 'Список регистраций',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'registrations': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'athlete_id': {'type': 'integer'},
                                'athlete_name': {'type': 'string'},
                                'category_id': {'type': 'integer'},
                                'category_name': {'type': 'string'},
                                'gender': {'type': 'string'},
                                'age': {'type': 'integer'},
                                'club': {'type': 'string'},
                                'registered_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Турнир не найден'
        }
    }
})
def get_tournament_registrations(tournament_id):
    """Получить список регистраций на турнир"""
    try:
        tournament = Tournament.query.get(tournament_id)
        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        registrations = []
        for category in tournament.categories:
            for athlete in category.athletes:
                # Получаем время регистрации из таблицы связи
                registration_time = db.session.query(category_athletes.c.registered_at).filter(
                    category_athletes.c.category_id == category.id,
                    category_athletes.c.athlete_id == athlete.id
                ).scalar()

                registrations.append({
                    'athlete_id': athlete.id,
                    'athlete_name': athlete.full_name,
                    'category_id': category.id,
                    'category_name': category.name,
                    'gender': category.gender,
                    'age': athlete.age,
                    'club': athlete.club.name if athlete.club else None,
                    'registered_at': registration_time.isoformat() if registration_time else None
                })

        return jsonify({
            'success': True,
            'registrations': registrations,
            'total': len(registrations)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении регистраций: {str(e)}'
        }), 500


@registrations_bp.route('/<int:category_id>/athletes', methods=['GET'])
@swag_from({
    'tags': ['Registrations'],
    'summary': 'Получить зарегистрированных атлетов в категории',
    'description': 'Возвращает список атлетов, зарегистрированных в конкретной категории',
    'parameters': [
        {
            'name': 'category_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID категории'
        }
    ],
    'responses': {
        200: {
            'description': 'Список атлетов в категории',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'category': {'type': 'string'},
                    'athletes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'full_name': {'type': 'string'},
                                'club': {'type': 'string'},
                                'age': {'type': 'integer'},
                                'rank': {'type': 'string'},
                                'weight': {'type': 'number'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Категория не найдена'
        }
    }
})
def get_category_registrations(category_id):
    """Получить зарегистрированных атлетов в категории"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        athletes_data = []
        for athlete in category.athletes:
            # Получаем последний вес атлета для этого турнира
            current_weight = athlete.get_current_weight(category.tournament_id)

            athletes_data.append({
                'id': athlete.id,
                'full_name': athlete.full_name,
                'club': athlete.club.name if athlete.club else None,
                'age': athlete.age,
                'rank': athlete.rank,
                'weight': current_weight
            })

        return jsonify({
            'success': True,
            'category': category.name,
            'athletes': athletes_data,
            'total': len(athletes_data)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении атлетов категории: {str(e)}'
        }), 500


@registrations_bp.route('/<int:category_id>/athlete/<int:athlete_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Registrations'],
    'summary': 'Отменить регистрацию атлета',
    'description': 'Удаляет атлета из категории (отмена регистрации)',
    'parameters': [
        {
            'name': 'category_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID категории'
        },
        {
            'name': 'athlete_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID атлета'
        }
    ],
    'responses': {
        200: {
            'description': 'Регистрация отменена'
        },
        404: {
            'description': 'Категория или атлет не найдены'
        },
        400: {
            'description': 'Ошибка при отмене регистрации'
        }
    }
})
def unregister_athlete(category_id, athlete_id):
    """Отменить регистрацию атлета"""
    try:
        category = Category.query.get(category_id)
        athlete = Athlete.query.get(athlete_id)

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        if not athlete:
            return jsonify({
                'success': False,
                'message': 'Атлет не найден'
            }), 404

        # Проверяем, зарегистрирован ли атлет
        if athlete not in category.athletes:
            return jsonify({
                'success': False,
                'message': 'Атлет не зарегистрирован в этой категории'
            }), 400

        # Удаляем регистрацию
        category.athletes.remove(athlete)

        # Используем save_to_db вместо ручного commit
        if category.save_to_db():
            return jsonify({
                'success': True,
                'message': 'Регистрация отменена'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при отмене регистрации'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при отмене регистрации: {str(e)}'
        }), 500