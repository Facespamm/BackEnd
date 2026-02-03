from flask import Blueprint, request, jsonify

from database.db import create_session
from new_model.head_model.new_athlete import AthleteNew
from new_model.weighing_new import WeighingNew
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository

weighing_bp = Blueprint('weighing', __name__, url_prefix='/weighing')
athlete_repo = AthleteRepository()
category_repo = CategoryRepository()
tournament_repo = TournamentRepository()

@weighing_bp.route('/', methods=['GET'])
def get_weighings():
    """Получить список взвешиваний"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        athlete_id = request.args.get('athlete_id', type=int)
        category_id = request.args.get('category_id', type=int)

        if not category_id or not tournament_id:
            return jsonify({
                'success': False,
                'message': "Не веденны category_id, tournament_id, athlete_id"
            })

        query = WeighingNew.query

        if tournament_id:
            tournament =  tournament_repo.get_tournament_category(tournament_id, category_id)
            query = query.filter_by(tournament_category_id=tournament.tournament_category_id)

        if athlete_id:
            query = query.filter_by(athlete_id=athlete_id)

        weighings = query.order_by(WeighingNew.weighing_time.desc()).all()


        result = []
        for weighing in weighings:

            athlete = athlete_repo.get_athlete_by_id(athlete_id)

            category = category_repo.get_category_by_id(weighing.weight_category)

            result.append({
                'id': weighing.id,
                'athlete_name': f'{athlete.user.first_name} {athlete.user.last_name} {athlete.user.middle_name}' if athlete.user else None,
                'weight': weighing.weight,
                'weight_category': {
                    'name': category.name,
                    'weight_range': f'от {category.min_weight} до {category.max_weight}',
                    'age-range': f'от {category.min_age} до {category.max_age}',
                    'gender': category.gender.value
                },
                'tournament_name': tournament_repo.get_tournament_name_by_tournament_category(weighing.tournament_category_id),
                'weighing_time': weighing.weighing_time.isoformat(),
                'status': _is_within_weight_category_limits(weighing),
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


@weighing_bp.route('/<int:weighing_id>/toggle-validation', methods=['PATCH'])
def toggle_weighing_validation(weighing_id):
    """Изменить статус валидации взвешивания"""
    try:
        session = create_session()
        weighing = session.query(WeighingNew).get(weighing_id)

        if not weighing:
            return jsonify({
                'success': False,
                'message': 'Взвешивание не найдено'
            }), 404

        # Меняем статус на противоположный
        weighing.is_valid = not weighing.is_valid

        session.commit()
        session.close()
        return jsonify({
            'success': True,
            'message': f'Статус валидации изменен на {"валидно" if weighing.is_valid else "невалидно"}',
            'is_valid': weighing.is_valid,
            'status_display': _is_within_weight_category_limits(weighing)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при изменении статуса валидации: {str(e)}'
        }), 500


@weighing_bp.route('/<int:weighing_id>', methods=['PUT'])
def update_weighing(weighing_id):
    """Обновить запись о взвешивании"""
    try:
        session = create_session()
        weighing = session.query(WeighingNew).get(weighing_id)

        if not weighing:
            return jsonify({
                'success': False,
                'message': 'Взвешивание не найдено'
            }), 404

        data = request.get_json()

        if 'weight' in data:
            weighing.weight = data['weight']

        if 'weight_category' in data:
            weighing.weight_category = data['weight_category']

        if 'is_valid' in data:
            weighing.is_valid = data['is_valid']

        if 'notes' in data:
            weighing.notes = data['notes']

        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'message': 'Взвешивание успешно обновлено',
            'weight_category': weighing.weight_category,
            'status': weighing.status_display,
            'is_valid': weighing.is_valid
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении взвешивания: {str(e)}'
        }), 500

@weighing_bp.route('/', methods=['POST'])
def create_weighing():
    """Создать запись о взвешивании"""
    try:
        session = create_session()
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('tournament_id') or  not data.get('category_id') or not data.get('athlete_id') or not data.get('weight') or not data.get('weight_category'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: tournament_id, athlete_id, weight'
            }), 400

        # Проверяем существование турнира и участника
        tournament = tournament_repo.get_tournament_category(data['tournament_id'], data['category_id'])
        athlete = AthleteNew.query.get(data['athlete_id'])

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

        weighing = WeighingNew(
            tournament_category_id=data['tournament_id'],
            athlete_id=data['athlete_id'],
            weight=data['weight'],
            notes=data.get('notes')
        )

        # Если указана весовая категория вручную - используем ее
        if data.get('weight_category'):
            weighing.weight_category = data['weight_category']

        session.commit()
        session.close()

        # ИСПРАВЛЕНО: используем save_to_db() вместо save()
        return jsonify({
            'success': True,
            'message': 'Взвешивание успешно записано',
            'weighing_id': weighing.id,
            'weight_category': weighing.weight_category,
        }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании записи взвешивания: {str(e)}'
        }), 500

def _is_within_weight_category_limits(weighing: "WeighingNew") -> bool:
    tc = weighing.tournament_categories
    if not tc or not tc.category:
        return False   # или True — зависит от бизнес-логики

    cat = tc.category

    if cat.min_weight is None or cat.max_weight is None:
        return False   # категория некорректно настроена

    return cat.min_weight <= weighing.weight <= cat.max_weight