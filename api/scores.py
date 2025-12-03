from flask import Blueprint, request, jsonify
from flasgger import swag_from
from services.score_manager import ScoreManager

scores_bp = Blueprint('scores', __name__, url_prefix='/api/scores')


@scores_bp.route('/fight/<int:fight_id>/yuko', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Добавить оценку ЮКО',
    'description': 'Добавляет оценку ЮКО для указанного спортсмена',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['athlete_color'],
                'properties': {
                    'athlete_color': {
                        'type': 'string',
                        'description': 'Цвет спортсмена',
                        'enum': ['WHITE', 'BLUE']
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Оценка добавлена'
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def add_yuko(fight_id):
    """Добавить оценку ЮКО"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }), 400

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_yuko(data['athlete_color'])

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500

@scores_bp.route('/fight/<int:fight_id>/events/batch', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Сохранить события боя пачкой',
    'description': 'Сохраняет все события боя одним запросом',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['events'],
                'properties': {
                    'events': {
                        'type': 'array',
                        'description': 'Список событий боя',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'type': {
                                    'type': 'string',
                                    'enum': ['SCORE', 'PENALTY', 'OSAEKOMI', 'TIMER', 'OTHER']
                                },
                                'subtype': {'type': 'string'},
                                'athlete_color': {
                                    'type': 'string',
                                    'enum': ['WHITE', 'BLUE', 'BOTH']
                                },
                                'timestamp': {'type': 'string'},
                                'match_time': {'type': 'string'},
                                'description': {'type': 'string'},
                                'details': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'События сохранены',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'},
                    'total_events': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def save_events_batch(fight_id):
    """Сохранить события боя пачкой"""
    try:
        data = request.get_json()

        if not data or 'events' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует список событий'
            }), 400

        score_manager = ScoreManager(fight_id)
        result = score_manager.save_fight_events(data['events'])

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/timeline', methods=['GET'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Получить хронологию боя',
    'description': 'Возвращает всю хронологию событий в бою',
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
            'description': 'Хронология боя',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'fight_id': {'type': 'integer'},
                    'events': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'type': {'type': 'string'},
                                'subtype': {'type': 'string'},
                                'athlete_color': {'type': 'string'},
                                'timestamp': {'type': 'string'},
                                'match_time': {'type': 'string'},
                                'description': {'type': 'string'},
                                'details': {'type': 'object'}
                            }
                        }
                    },
                    'summary': {'type': 'object'}
                }
            }
        },
        404: {
            'description': 'Схватка не найдена'
        }
    }
})
def get_fight_timeline(fight_id):
    """Получить хронологию боя"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.get_fight_timeline()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/summary', methods=['GET'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Получить сводку матча',
    'description': 'Возвращает сводку матча с группировкой по спортсменам',
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
            'description': 'Сводка матча',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'fight_id': {'type': 'integer'},
                    'summary': {
                        'type': 'object',
                        'properties': {
                            'white': {'type': 'object'},
                            'blue': {'type': 'object'},
                            'match_events': {'type': 'array'},
                            'timeline': {'type': 'array'}
                        }
                    },
                    'victory_type': {'type': 'string'},
                    'winner_id': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Схватка не найдена'
        }
    }
})
def get_match_summary(fight_id):
    """Получить сводку матча"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.get_match_summary()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500

@scores_bp.route('/fight/<int:fight_id>/wazaari', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Добавить оценку ВАЗА-АРИ',
    'description': 'Добавляет оценку ВАЗА-АРИ для указанного спортсмена',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['athlete_color'],
                'properties': {
                    'athlete_color': {
                        'type': 'string',
                        'description': 'Цвет спортсмена',
                        'enum': ['WHITE', 'BLUE']
                    },
                    'technique': {
                        'type': 'string',
                        'description': 'Использованная техника'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Оценка добавлена'
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def add_wazaari(fight_id):
    """Добавить оценку ВАЗА-АРИ"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }), 400

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_wazaari(
            data['athlete_color'],
            data.get('technique')
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/ippon', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Добавить оценку ИППОН',
    'description': 'Добавляет оценку ИППОН для указанного спортсмена и завершает бой',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['athlete_color'],
                'properties': {
                    'athlete_color': {
                        'type': 'string',
                        'description': 'Цвет спортсмена',
                        'enum': ['WHITE', 'BLUE']
                    },
                    'technique': {
                        'type': 'string',
                        'description': 'Использованная техника'
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'ИППОН добавлен, бой завершен'
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def add_ippon(fight_id):
    """Добавить оценку ИППОН"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }), 400

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_ippon(
            data['athlete_color'],
            data.get('technique')
        )

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/osaekomi/start', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Начать отсчет времени удержания (ОСАЕКОМИ)',
    'description': 'Начинает отсчет времени удержания для указанного спортсмена',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['athlete_color'],
                'properties': {
                    'athlete_color': {
                        'type': 'string',
                        'description': 'Цвет атакующего спортсмена',
                        'enum': ['WHITE', 'BLUE']
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Отсчет ОСАЕКОМИ начат'
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def start_osaekomi(fight_id):
    """Начать отсчет ОСАЕКОМИ"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }), 400

        score_manager = ScoreManager(fight_id)
        result = score_manager.start_osaekomi(data['athlete_color'])

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/osaekomi/stop', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Остановить отсчет времени удержания (ОСАЕКОМИ)',
    'description': 'Останавливает отсчет времени удержания и начисляет оценку',
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
            'description': 'ОСАЕКОМИ остановлен, оценка начислена'
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def stop_osaekomi(fight_id):
    """Остановить отсчет ОСАЕКОМИ"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.stop_osaekomi()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/penalty', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Добавить штраф',
    'description': 'Добавляет штраф для указанного спортсмена',
    'parameters': [
        {
            'name': 'fight_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID схватки'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['athlete_color', 'penalty_type'],
                'properties': {
                    'athlete_color': {
                        'type': 'string',
                        'description': 'Цвет спортсмена',
                        'enum': ['WHITE', 'BLUE']
                    },
                    'penalty_type': {
                        'type': 'string',
                        'description': 'Тип штрафа',
                        'enum': ['SHIDO', 'HANSOKU_MAKE']
                    }
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Штраф добавлен'
        },
        400: {
            'description': 'Ошибка валидации'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def add_penalty(fight_id):
    """Добавить штраф"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data or 'penalty_type' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color или penalty_type'
            }), 400

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_penalty(data['athlete_color'], data['penalty_type'])

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/undo', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Отменить последнее действие',
    'description': 'Отменяет последнее действие (оценку или штраф)',
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
            'description': 'Действие отменено'
        },
        400: {
            'description': 'Не удалось отменить действие'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def undo_action(fight_id):
    """Отменить последнее действие"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.undo_last_action()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/reset', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Сбросить все оценки',
    'description': 'Сбрасывает все оценки и штрафы в схватке',
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
            'description': 'Все оценки сброшены'
        },
        400: {
            'description': 'Не удалось сбросить оценки'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def reset_scores(fight_id):
    """Сбросить все оценки"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.reset_scores()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/current', methods=['GET'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Получить текущие оценки',
    'description': 'Возвращает текущие оценки, штрафы и состояние ОСАЕКОМИ',
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
            'description': 'Текущие оценки',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'white': {
                        'type': 'object',
                        'properties': {
                            'score': {'type': 'integer'},
                            'yuko': {'type': 'integer'},
                            'wazaari': {'type': 'integer'},
                            'ippon': {'type': 'integer'},
                            'penalty_count': {'type': 'integer'}
                        }
                    },
                    'blue': {
                        'type': 'object',
                        'properties': {
                            'score': {'type': 'integer'},
                            'yuko': {'type': 'integer'},
                            'wazaari': {'type': 'integer'},
                            'ippon': {'type': 'integer'},
                            'penalty_count': {'type': 'integer'}
                        }
                    },
                    'osaekomi': {
                        'type': 'object',
                        'properties': {
                            'active': {'type': 'boolean'},
                            'athlete_color': {'type': 'string'},
                            'time': {'type': 'integer'}
                        }
                    },
                    'victory_type': {'type': 'string'},
                    'winner_id': {'type': 'integer'},
                    'fight_status': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Схватка не найдена'
        }
    }
})
def get_current_scores(fight_id):
    """Получить текущие оценки"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.get_current_scores()

        return jsonify(result), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500


@scores_bp.route('/fight/<int:fight_id>/golden-score', methods=['POST'])
@swag_from({
    'tags': ['Scores'],
    'summary': 'Перейти в золотой скор',
    'description': 'Переводит схватку в режим золотого скора',
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
            'description': 'Переход в золотой скор выполнен'
        },
        400: {
            'description': 'Не удалось перейти в золотой скор'
        },
        404: {
            'description': 'Схватка не найдена'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def enter_golden_score(fight_id):
    """Перейти в золотой скор"""
    try:
        from models.fight import Fight

        fight = Fight.query.get(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }), 404

        if fight.enter_golden_score():
            return jsonify({
                'success': True,
                'message': 'Переход в золотой скор выполнен',
                'timer_seconds': fight.timer_seconds,
                'is_golden_score': fight.is_golden_score
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Не удалось перейти в золотой скор. Проверьте статус схватки и время.'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }), 500