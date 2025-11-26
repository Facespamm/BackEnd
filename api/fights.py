from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime
from models.fight import Fight
from models.tournament import Tournament
from models.athlete import Athlete
from services.fight_manager import FightManager
from sqlalchemy.exc import IntegrityError

fights_bp = Blueprint('fights', __name__, url_prefix='/fights')


@fights_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Fights'],
    'summary': 'Получить список схваток',
    'description': 'Возвращает список схваток с возможностью фильтрации',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'ID турнира для фильтрации'
        },
        {
            'name': 'status',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Статус схватки',
            'enum': ['SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']
        },
        {
            'name': 'tatami',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'Номер татами'
        }
    ],
    'responses': {
        200: {
            'description': 'Список схваток получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'fights': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'tournament_id': {'type': 'integer'},
                                'tatami': {'type': 'integer'},
                                'status': {'type': 'string'},
                                'round_number': {'type': 'integer'},
                                'fight_number': {'type': 'integer'},
                                'scheduled_time': {'type': 'string', 'format': 'date-time'},
                                'timer_seconds': {'type': 'integer'},
                                'is_golden_score': {'type': 'boolean'},
                                'white_athlete': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer'},
                                        'name': {'type': 'string'}
                                    }
                                },
                                'blue_athlete': {
                                    'type': 'object',
                                    'properties': {
                                        'id': {'type': 'integer'},
                                        'name': {'type': 'string'}
                                    }
                                }
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
def get_fights():
    """Получить список схваток"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        status = request.args.get('status')
        tatami = request.args.get('tatami', type=int)

        query = Fight.query

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)

        if status:
            query = query.filter_by(status=status)

        if tatami:
            query = query.filter_by(tatami=tatami)

        fights = query.order_by(Fight.tatami, Fight.scheduled_time).all()

        result = []
        for fight in fights:
            fight_data = {
                'id': fight.id,
                'tournament_id': fight.tournament_id,
                'tatami': fight.tatami,
                'status': fight.status,
                'round_number': fight.round_number,
                'fight_number': fight.fight_number,
                'scheduled_time': fight.scheduled_time.isoformat() if fight.scheduled_time else None,
                'timer_seconds': fight.timer_seconds,
                'is_golden_score': fight.is_golden_score,
                'white_athlete': None,
                'blue_athlete': None
            }

            if fight.white_athlete:
                fight_data['white_athlete'] = {
                    'id': fight.white_athlete.id,
                    'name': fight.white_athlete.full_name
                }

            if fight.blue_athlete:
                fight_data['blue_athlete'] = {
                    'id': fight.blue_athlete.id,
                    'name': fight.blue_athlete.full_name
                }

            result.append(fight_data)

        return jsonify({
            'success': True,
            'fights': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении схваток: {str(e)}'
        }), 500


@fights_bp.route('/', methods=['POST'])
@swag_from({
    'tags': ['Fights'],
    'summary': 'Создать схватку',
    'description': 'Создает новую схватку',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['tournament_id'],
                'properties': {
                    'tournament_id': {
                        'type': 'integer',
                        'description': 'ID турнира'
                    },
                    'white_athlete_id': {
                        'type': 'integer',
                        'description': 'ID спортсмена в белом'
                    },
                    'blue_athlete_id': {
                        'type': 'integer',
                        'description': 'ID спортсмена в синем'
                    },
                    'tatami': {
                        'type': 'integer',
                        'description': 'Номер татами'
                    },
                    'scheduled_time': {
                        'type': 'string',
                        'format': 'date-time',
                        'description': 'Запланированное время (ISO формат)'
                    },
                    'round_number': {
                        'type': 'integer',
                        'description': 'Номер раунда'
                    },
                    'fight_number': {
                        'type': 'integer',
                        'description': 'Номер схватки'
                    }
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Схватка успешно создана',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'fight_id': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Турнир или спортсмен не найден'
        },
        409: {
            'description': 'Конфликт - схватка с такими параметрами уже существует'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def create_fight():
    """Создать схватку"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('tournament_id'):
            return jsonify({
                'success': False,
                'message': 'Обязательное поле: tournament_id'
            }), 400

        # Проверяем существование турнира
        tournament = Tournament.query.get(data['tournament_id'])
        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        # Проверяем существование спортсменов
        if data.get('white_athlete_id'):
            white_athlete = Athlete.query.get(data['white_athlete_id'])
            if not white_athlete:
                return jsonify({
                    'success': False,
                    'message': f'Спортсмен с ID {data["white_athlete_id"]} не найден'
                }), 404

        if data.get('blue_athlete_id'):
            blue_athlete = Athlete.query.get(data['blue_athlete_id'])
            if not blue_athlete:
                return jsonify({
                    'success': False,
                    'message': f'Спортсмен с ID {data["blue_athlete_id"]} не найден'
                }), 404

        # Проверяем, что один спортсмен не борется сам с собой
        if (data.get('white_athlete_id') and data.get('blue_athlete_id') and
                data['white_athlete_id'] == data['blue_athlete_id']):
            return jsonify({
                'success': False,
                'message': 'Спортсмен не может бороться сам с собой'
            }), 400

        # Проверяем уникальность схватки (если есть tatami, round_number и fight_number)
        if data.get('tatami') and data.get('round_number') and data.get('fight_number'):
            existing_fight = Fight.query.filter_by(
                tournament_id=data['tournament_id'],
                tatami=data['tatami'],
                round_number=data['round_number'],
                fight_number=data['fight_number']
            ).first()

            if existing_fight:
                return jsonify({
                    'success': False,
                    'message': f'Схватка с такими параметрами уже существует (ID: {existing_fight.id})'
                }), 409

        fight = Fight(
            tournament_id=data['tournament_id'],
            white_athlete_id=data.get('white_athlete_id'),
            blue_athlete_id=data.get('blue_athlete_id'),
            tatami=data.get('tatami'),
            round_number=data.get('round_number'),
            fight_number=data.get('fight_number')
        )

        if data.get('scheduled_time'):
            fight.scheduled_time = datetime.fromisoformat(data['scheduled_time'])

        if fight.save_to_db():
            return jsonify({
                'success': True,
                'message': 'Схватка успешно создана',
                'fight_id': fight.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении схватки'
            }), 400

    except IntegrityError as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка целостности данных: возможно схватка с такими параметрами уже существует'
        }), 409
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Неверный формат данных: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании схватки: {str(e)}'
        }), 500


@fights_bp.route('/<int:fight_id>', methods=['GET'])
@swag_from({
    'tags': ['Fights'],
    'summary': 'Получить информацию о схватке',
    'description': 'Возвращает детальную информацию о конкретной схватке',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        }
    ],
    'responses': {
        200: {
            'description': 'Информация о схватке',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'tournament_id': {'type': 'integer'},
                    'tatami': {'type': 'integer'},
                    'status': {'type': 'string'},
                    'round_number': {'type': 'integer'},
                    'fight_number': {'type': 'integer'},
                    'scheduled_time': {'type': 'string'},
                    'timer_seconds': {'type': 'integer'},
                    'is_golden_score': {'type': 'boolean'},
                    'white_athlete': {'type': 'object'},
                    'blue_athlete': {'type': 'object'}
                }
            }
        },
        404: {
            'description': 'Схватка не найдена'
        }
    }
})
def get_fight(fight_id):
    """Получить информацию о схватке"""
    try:
        fight = Fight.query.get(fight_id)

        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        fight_data = {
            'id': fight.id,
            'tournament_id': fight.tournament_id,
            'tatami': fight.tatami,
            'status': fight.status,
            'round_number': fight.round_number,
            'fight_number': fight.fight_number,
            'scheduled_time': fight.scheduled_time.isoformat() if fight.scheduled_time else None,
            'timer_seconds': fight.timer_seconds,
            'is_golden_score': fight.is_golden_score,
            'white_athlete': None,
            'blue_athlete': None
        }

        if fight.white_athlete:
            fight_data['white_athlete'] = {
                'id': fight.white_athlete.id,
                'name': fight.white_athlete.full_name
            }

        if fight.blue_athlete:
            fight_data['blue_athlete'] = {
                'id': fight.blue_athlete.id,
                'name': fight.blue_athlete.full_name
            }

        return jsonify(fight_data), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении схватки: {str(e)}'
        }), 500


@fights_bp.route('/<int:fight_id>/start', methods=['POST'])
@swag_from({
    'tags': ['Fights'],
    'summary': 'Начать схватку',
    'description': 'Начинает схватку и запускает таймер',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        }
    ],
    'responses': {
        200: {
            'description': 'Схватка начата',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Не удалось начать схватку'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def start_fight(fight_id):
    """Начать схватку"""
    try:
        fight = Fight.query.get(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        fight_manager = FightManager(fight_id)

        if fight_manager.start_fight():
            return jsonify({
                'success': True,
                'message': 'Схватка начата'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Не удалось начать схватку'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при запуске схватки: {str(e)}'
        }), 500


@fights_bp.route('/<int:fight_id>/pause', methods=['POST'])
@swag_from({
    'tags': ['Fights'],
    'summary': 'Приостановить схватку',
    'description': 'Приостанавливает таймер схватки',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        }
    ],
    'responses': {
        200: {
            'description': 'Схватка приостановлена'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def pause_fight(fight_id):
    """Приостановить схватку"""
    try:
        fight = Fight.query.get(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        fight_manager = FightManager(fight_id)

        if fight_manager.pause_fight():
            return jsonify({
                'success': True,
                'message': 'Схватка приостановлена'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Не удалось приостановить схватку'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при приостановке схватки: {str(e)}'
        }), 500


@fights_bp.route('/<int:fight_id>/finish', methods=['POST'])
@swag_from({
    'tags': ['Fights'],
    'summary': 'Завершить схватку',
    'description': 'Завершает схватку',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        }
    ],
    'responses': {
        200: {
            'description': 'Схватка завершена'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def finish_fight(fight_id):
    """Завершить схватку"""
    try:
        fight = Fight.query.get(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        fight_manager = FightManager(fight_id)

        if fight_manager.finish_fight():
            return jsonify({
                'success': True,
                'message': 'Схватка завершена'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Не удалось завершить схватку'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при завершении схватки: {str(e)}'
        }), 500