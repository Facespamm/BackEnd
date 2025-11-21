from flask import Blueprint, request, jsonify
from flasgger import swag_from
from models.result import Result
from models.fight import Fight
from models.category import Category
from services.result_calculator import ResultCalculator

results_bp = Blueprint('results', __name__, url_prefix='/results')


@results_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Results'],
    'summary': 'Получить список результатов',
    'description': 'Возвращает список результатов с возможностью фильтрации по турниру',
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
            'description': 'Список результатов получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'fight_id': {'type': 'integer'},
                                'winner_name': {'type': 'string'},
                                'victory_type': {'type': 'string'},
                                'victory_description': {'type': 'string'},
                                'fight_duration': {'type': 'integer'},
                                'technique_used': {'type': 'string'}
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
def get_results():
    """Получить список результатов"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)

        query = Result.query

        if tournament_id:
            query = query.join(Fight).filter(Fight.tournament_id == tournament_id)

        results = query.all()

        result_data = []
        for result in results:
            result_data.append({
                'id': result.id,
                'fight_id': result.fight_id,
                'winner_name': result.winner.full_name if result.winner else None,
                'victory_type': result.victory_type,
                'victory_description': result.victory_description,
                'fight_duration': result.fight_duration,
                'technique_used': result.technique_used
            })

        return jsonify({
            'success': True,
            'results': result_data,
            'total': len(result_data)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении результатов: {str(e)}'
        }), 500


@results_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Results'],
    'summary': 'Создать результат боя',
    'description': 'Создает новый результат для боя',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['fight_id', 'winner_id', 'victory_type'],
                'properties': {
                    'fight_id': {
                        'type': 'integer',
                        'description': 'ID боя'
                    },
                    'winner_id': {
                        'type': 'integer',
                        'description': 'ID победителя'
                    },
                    'victory_type': {
                        'type': 'string',
                        'description': 'Тип победы',
                        'enum': ['IPPON', 'WAZA_ARI', 'DECISION', 'DISQUALIFICATION', 'FORFEIT']
                    },
                    'details': {
                        'type': 'string',
                        'description': 'Дополнительные детали'
                    },
                    'fight_duration': {
                        'type': 'integer',
                        'description': 'Длительность боя в секундах'
                    },
                    'technique_used': {
                        'type': 'string',
                        'description': 'Использованная техника'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Результат успешно создан',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'result_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Бой не найден'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def create_result():
    """Создать результат боя"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('fight_id') or not data.get('winner_id') or not data.get('victory_type'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: fight_id, winner_id, victory_type'
            }), 400

        # Проверяем существование боя
        fight = Fight.query.get(data['fight_id'])
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Бой не найден'
            }), 404

        result = Result(
            fight_id=data['fight_id'],
            winner_id=data['winner_id'],
            victory_type=data['victory_type'],
            details=data.get('details'),
            fight_duration=data.get('fight_duration'),
            technique_used=data.get('technique_used')
        )

        if result.save():
            return jsonify({
                'success': True,
                'message': 'Результат успешно создан',
                'result_id': result.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении результата'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании результата: {str(e)}'
        }), 500


@results_bp.route('/tournament/<int:tournament_id>', methods=['GET'])
@swag_from({
    'tags': ['Results'],
    'summary': 'Получить результаты турнира',
    'description': 'Возвращает полные результаты турнира по категориям и командный зачет',
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
            'description': 'Результаты турнира',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'categories_results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'category': {'type': 'string'},
                                'results': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'place': {'type': 'integer'},
                                            'athlete_name': {'type': 'string'},
                                            'club': {'type': 'string'},
                                            'wins': {'type': 'integer'},
                                            'losses': {'type': 'integer'}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'team_ranking': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'place': {'type': 'integer'},
                                'club_name': {'type': 'string'},
                                'points': {'type': 'number'},
                                'gold': {'type': 'integer'},
                                'silver': {'type': 'integer'},
                                'bronze': {'type': 'integer'}
                            }
                        }
                    }
                }
            }
        },
        404: {
            'description': 'Турнир не найден'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def get_tournament_results(tournament_id):
    """Получить результаты турнира"""
    try:
        calculator = ResultCalculator(tournament_id)

        # Результаты по категориям
        categories_results = []
        for category in Category.query.filter_by(tournament_id=tournament_id).all():
            results = calculator.calculate_category_results(category.id)
            if results:
                categories_results.append({
                    'category': category.name,
                    'results': results
                })

        # Командный зачет
        team_ranking = calculator.calculate_team_ranking()

        return jsonify({
            'success': True,
            'categories_results': categories_results,
            'team_ranking': team_ranking
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении результатов турнира: {str(e)}'
        }), 500


@results_bp.route('/<int:result_id>', methods=['GET'])
@swag_from({
    'tags': ['Results'],
    'summary': 'Получить конкретный результат',
    'description': 'Возвращает детальную информацию о результате боя',
    'parameters': [
        {
            'name': 'result_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID результата'
        }
    ],
    'responses': {
        200: {
            'description': 'Информация о результате',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'fight_id': {'type': 'integer'},
                    'winner_name': {'type': 'string'},
                    'victory_type': {'type': 'string'},
                    'victory_description': {'type': 'string'},
                    'fight_duration': {'type': 'integer'},
                    'technique_used': {'type': 'string'},
                    'details': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Результат не найден'
        }
    }
})
def get_result(result_id):
    """Получить конкретный результат"""
    try:
        result = Result.query.get(result_id)

        if not result:
            return jsonify({
                'success': False,
                'message': 'Результат не найден'
            }), 404

        return jsonify({
            'id': result.id,
            'fight_id': result.fight_id,
            'winner_name': result.winner.full_name if result.winner else None,
            'victory_type': result.victory_type,
            'victory_description': result.victory_description,
            'fight_duration': result.fight_duration,
            'technique_used': result.technique_used,
            'details': result.details
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении результата: {str(e)}'
        }), 500