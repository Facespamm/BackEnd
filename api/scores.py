# scores.py
from flask import Blueprint, request, jsonify, Response
from flasgger import swag_from
from services.score_manager import ScoreManager
import json  # Добавляем импорт

scores_bp = Blueprint('scores', __name__, url_prefix='/api/scores')


@scores_bp.route('/fight/<int:fight_id>/yuko', methods=['POST'])
def add_yuko(fight_id):
    """Добавить оценку ЮКО"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }, 400)

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
def save_events_batch(fight_id):
    """Сохранить события боя пачкой"""
    try:
        data = request.get_json()

        if not data or 'events' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует список событий'
            }, 400)

        score_manager = ScoreManager(fight_id)
        result = score_manager.save_fight_events(data['events'])

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/timeline', methods=['GET'])
def get_fight_timeline(fight_id):
    """Получить хронологию боя"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.get_fight_timeline()

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/summary', methods=['GET'])
def get_match_summary(fight_id):
    """Получить сводку матча"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.get_match_summary()

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)

@scores_bp.route('/fight/<int:fight_id>/wazaari', methods=['POST'])
def add_wazaari(fight_id):
    """Добавить оценку ВАЗА-АРИ"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }, 400)

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_wazaari(
            data['athlete_color'],
            data.get('technique')
        )

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/ippon', methods=['POST'])
def add_ippon(fight_id):
    """Добавить оценку ИППОН"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }, 400)

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_ippon(
            data['athlete_color'],
            data.get('technique')
        )

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/osaekomi/start', methods=['POST'])
def start_osaekomi(fight_id):
    """Начать отсчет ОСАЕКОМИ"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color'
            }, 400)

        score_manager = ScoreManager(fight_id)
        result = score_manager.start_osaekomi(data['athlete_color'])

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/osaekomi/stop', methods=['POST'])
def stop_osaekomi(fight_id):
    """Остановить отсчет ОСАЕКОМИ"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.stop_osaekomi()

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/penalty', methods=['POST'])
def add_penalty(fight_id):
    """Добавить штраф"""
    try:
        data = request.get_json()

        if not data or 'athlete_color' not in data or 'penalty_type' not in data:
            return jsonify({
                'success': False,
                'message': 'Отсутствует athlete_color или penalty_type'
            }, 400)

        score_manager = ScoreManager(fight_id)
        result = score_manager.add_penalty(data['athlete_color'], data['penalty_type'])

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/undo', methods=['POST'])
def undo_action(fight_id):
    """Отменить последнее действие"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.undo_last_action()

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/reset', methods=['POST'])
def reset_scores(fight_id):
    """Сбросить все оценки"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.reset_scores()

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/current', methods=['GET'])
def get_current_scores(fight_id):
    """Получить текущие оценки"""
    try:
        score_manager = ScoreManager(fight_id)
        result = score_manager.get_current_scores()

        return jsonify(result, 200)

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }, 404)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)


@scores_bp.route('/fight/<int:fight_id>/golden-score', methods=['POST'])
def enter_golden_score(fight_id):
    """Перейти в золотой скор"""
    try:
        from models.fight import Fight

        fight = Fight.query.get(fight_id)
        if not fight:
            return jsonify({
                'success': False,
                'message': 'Схватка не найдена'
            }, 404)

        if fight.enter_golden_score():
            return jsonify({
                'success': True,
                'message': 'Переход в золотой скор выполнен',
                'timer_seconds': fight.timer_seconds,
                'is_golden_score': fight.is_golden_score
            }, 200)
        else:
            return jsonify({
                'success': False,
                'message': 'Не удалось перейти в золотой скор. Проверьте статус схватки и время.'
            }, 400)

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        }, 500)