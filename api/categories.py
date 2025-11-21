from flask import Blueprint, request, jsonify
from flasgger import swag_from
from models.category import Category
from models.tournament import Tournament

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')


@categories_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Categories'],
    'summary': 'Получить список категорий',
    'description': 'Возвращает список категорий с возможностью фильтрации по турниру',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'ID турнира для фильтрации'
        }
    ],
    'responses': {
        200: {
            'description': 'Список категорий получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'categories': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'gender': {'type': 'string'},
                                'weight_range': {'type': 'string'},
                                'age_range': {'type': 'string'},
                                'athletes_count': {'type': 'integer'},
                                'tournament_id': {'type': 'integer'}
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
def get_categories():
    """Получить список категорий"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)

        query = Category.query

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        categories = query.filter_by(is_active=True).all()

        result = []
        for category in categories:
            result.append({
                'id': category.id,
                'name': category.name,
                'gender': category.gender,
                'weight_range': category.weight_range,
                'age_range': category.age_range,
                'athletes_count': category.athletes_count,
                'tournament_id': category.tournament_id
            })

        return jsonify({
            'success': True,
            'categories': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении категорий: {str(e)}'
        }), 500


@categories_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Categories'],
    'summary': 'Создать новую категорию',
    'description': 'Создает новую категорию для турнира',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['tournament_id', 'name', 'gender'],
                'properties': {
                    'tournament_id': {
                        'type': 'integer',
                        'description': 'ID турнира'
                    },
                    'name': {
                        'type': 'string',
                        'description': 'Название категории'
                    },
                    'gender': {
                        'type': 'string',
                        'description': 'Пол',
                        'enum': ['MALE', 'FEMALE', 'MIXED']
                    },
                    'min_weight': {
                        'type': 'number',
                        'format': 'float',
                        'description': 'Минимальный вес в кг'
                    },
                    'max_weight': {
                        'type': 'number',
                        'format': 'float',
                        'description': 'Максимальный вес в кг'
                    },
                    'min_age': {
                        'type': 'integer',
                        'description': 'Минимальный возраст'
                    },
                    'max_age': {
                        'type': 'integer',
                        'description': 'Максимальный возраст'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Категория успешно создана',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'category_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Турнир не найден'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def create_category():
    """Создать новую категорию"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('name') or not data.get('tournament_id') or not data.get('gender'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: name, tournament_id, gender'
            }), 400

        # Проверяем существование турнира
        tournament = Tournament.query.get(data['tournament_id'])
        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        category = Category(
            tournament_id=data['tournament_id'],
            name=data['name'],
            gender=data['gender'],
            min_weight=data.get('min_weight'),
            max_weight=data.get('max_weight'),
            min_age=data.get('min_age'),
            max_age=data.get('max_age')
        )

        if category.save():
            return jsonify({
                'success': True,
                'message': 'Категория успешно создана',
                'category_id': category.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении категории'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании категории: {str(e)}'
        }), 500


@categories_bp.route('/<int:category_id>', methods=['GET'])
@swag_from({
    'tags': ['Categories'],
    'summary': 'Получить информацию о категории',
    'description': 'Возвращает детальную информацию о конкретной категории',
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
            'description': 'Информация о категории',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'gender': {'type': 'string'},
                    'min_weight': {'type': 'number'},
                    'max_weight': {'type': 'number'},
                    'min_age': {'type': 'integer'},
                    'max_age': {'type': 'integer'},
                    'weight_range': {'type': 'string'},
                    'age_range': {'type': 'string'},
                    'athletes_count': {'type': 'integer'},
                    'tournament_id': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Категория не найдена'
        }
    }
})
def get_category(category_id):
    """Получить информацию о категории"""
    try:
        category = Category.query.get(category_id)

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        return jsonify({
            'id': category.id,
            'name': category.name,
            'gender': category.gender,
            'min_weight': category.min_weight,
            'max_weight': category.max_weight,
            'min_age': category.min_age,
            'max_age': category.max_age,
            'weight_range': category.weight_range,
            'age_range': category.age_range,
            'athletes_count': category.athletes_count,
            'tournament_id': category.tournament_id
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении категории: {str(e)}'
        }), 500


@categories_bp.route('/<int:category_id>', methods=['PUT'])
@swag_from({
    'tags': ['Categories'],
    'summary': 'Обновить категорию',
    'description': 'Обновляет данные категории',
    'parameters': [
        {
            'name': 'category_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID категории'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'gender': {'type': 'string', 'enum': ['MALE', 'FEMALE', 'MIXED']},
                    'min_weight': {'type': 'number'},
                    'max_weight': {'type': 'number'},
                    'min_age': {'type': 'integer'},
                    'max_age': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Категория успешно обновлена'
        },
        404: {
            'description': 'Категория не найдена'
        },
        400: {
            'description': 'Ошибка при обновлении'
        }
    }
})
def update_category(category_id):
    """Обновить категорию"""
    try:
        category = Category.query.get(category_id)

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        # Обновляем поля
        for key, value in data.items():
            if hasattr(category, key):
                setattr(category, key, value)

        if category.save():
            return jsonify({
                'success': True,
                'message': 'Категория успешно обновлена',
                'category_id': category.id
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при обновлении категории'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении категории: {str(e)}'
        }), 500


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@swag_from({
    'tags': ['Categories'],
    'summary': 'Удалить категорию',
    'description': 'Удаляет категорию из системы',
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
            'description': 'Категория успешно удалена'
        },
        404: {
            'description': 'Категория не найдена'
        },
        400: {
            'description': 'Ошибка при удалении'
        }
    }
})
def delete_category(category_id):
    """Удалить категорию"""
    try:
        category = Category.query.get(category_id)

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        if category.delete():
            return jsonify({
                'success': True,
                'message': 'Категория удалена'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при удалении категории'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении категории: {str(e)}'
        }), 500


@categories_bp.route('/<int:category_id>/athletes', methods=['GET'])
@swag_from({
    'tags': ['Categories'],
    'summary': 'Получить участников категории',
    'description': 'Возвращает список всех участников в категории',
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
            'description': 'Список участников категории',
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
                                'rank': {'type': 'string'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Категория не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def get_category_athletes(category_id):
    """Получить участников категории"""
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        athletes = []
        for athlete in category.athletes:
            athletes.append({
                'id': athlete.id,
                'full_name': athlete.full_name,
                'club': athlete.club.name if athlete.club else None,
                'age': athlete.age,
                'rank': athlete.rank
            })

        return jsonify({
            'success': True,
            'category': category.name,
            'athletes': athletes,
            'total': len(athletes)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участников категории: {str(e)}'
        }), 500