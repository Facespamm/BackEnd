from flask import Blueprint, request, jsonify
from sqlalchemy import update

from database.db import create_session
from models import athlete
from new_model.head_model.new_athlete import AthleteNew
from new_model.new_associations import AthleteRegistration, TournamentCategory
from new_model.weighing_new import WeighingNew
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository
from repository.weight_repo import WeightRepository

weighing_bp = Blueprint('weighing', __name__, url_prefix='/api/weighing')


@weighing_bp.route('/', methods=['GET'])
def get_weighings():
    """Получить список взвешиваний"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        athlete_id    = request.args.get('athlete_id', type=int)
        category_id   = request.args.get('category_id', type=int)

        if not category_id or not tournament_id:
            return jsonify({'success': False, 'message': 'Не введены category_id, tournament_id'}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_category(tournament_id, category_id)
            if not tournament:
                return jsonify({'message': 'Нет такой категории в турнире'}), 404

            weighing_repo  = WeightRepository(session)
            athlete_repo   = AthleteRepository(session)
            category_repo  = CategoryRepository(session)

            weighings = weighing_repo.get_weights(tournament.tournament_category_id, athlete_id)

            result = []
            for weighing in weighings:
                athlete = athlete_repo.get_athlete_by_id(weighing.athlete_id)
                athlete_name = None
                if athlete and athlete.user:
                    athlete_name = f'{athlete.user.first_name} {athlete.user.last_name} {athlete.user.middle_name or ""}'.strip()

                category = category_repo.get_category_by_id(weighing.weight_category)
                tournament_name = tournament_repo.get_tournament_name_by_tournament_category(weighing.tournament_category_id)
                status = _is_within_weight_category_limits(weighing)

                result.append({
                    'id': weighing.id,
                    'athlete_name': athlete_name or 'Атлет не найден',
                    'weight': weighing.weight,
                    'weight_category': {
                        'name': category.name,
                        'weight_range': f'от {category.min_weight} до {category.max_weight}',
                        'age-range': f'от {category.min_year} до {category.max_year}',
                        'gender': category.gender.value
                    } if category else None,
                    'tournament_name': tournament_name,
                    'weighing_time': weighing.weighing_time.isoformat(),
                    'status': status,
                    'is_valid': weighing.is_valid
                })

        return jsonify({'success': True, 'weighings': result, 'total': len(result)}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при получении взвешиваний: {str(e)}'}), 500


@weighing_bp.route('/<int:weighing_id>/toggle-validation', methods=['PATCH'])
def toggle_weighing_validation(weighing_id):
    try:
        with create_session() as session:
            weighing_repo = WeightRepository(session)
            weighing = weighing_repo.get_weight(weighing_id)
            if not weighing:
                return jsonify({'success': False, 'message': 'Взвешивание не найдено'}), 404

            is_change = weighing_repo.change_weighing_validation(weighing_id)

            # ✅ Читаем is_valid ВНУТРИ сессии
            is_valid = weighing.is_valid
            status_display = _is_within_weight_category_limits(weighing)

        if is_change:
            return jsonify({
                'success': True,
                'message': f'Статус изменен на {"валидно" if is_valid else "невалидно"}',
                'is_valid': is_valid,
                'status_display': status_display
            }), 200
        return jsonify({'message': 'Не получилось обновить статус'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при изменении статуса: {str(e)}'}), 500


@weighing_bp.route('/<int:weighing_id>', methods=['PUT'])
def update_weighing(weighing_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Нет данных для изменения'}), 400

        with create_session() as session:
            weighing_repo = WeightRepository(session)
            weighing = weighing_repo.get_weight(weighing_id)
            if not weighing:
                return jsonify({'success': False, 'message': 'Взвешивание не найдено'}), 404

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_weight(weighing_id)

            if '-' in category.name:
                if category.min_weight <= data['weight'] <= category.max_weight:
                    is_update = weighing_repo.update_weighing_information(weighing_id, data)
                else:
                    return jsonify({'success':False, 'message': f'Вес не подходить для такой категории {category.name}'}), 400
            elif '+' in category.name:
                if category.min_weight >= data['weight']:
                    is_update = weighing_repo.update_weighing_information(weighing_id, data)
                else:
                    return jsonify({'success':False, 'message': f'Вес не подходить для такой категории {category.name}'}), 400

            # ✅ Читаем данные ВНУТРИ сессии
            weight_category = weighing.weight_category
            is_valid = weighing.is_valid

        if is_update:
            return jsonify({
                'success': True,
                'message': 'Взвешивание успешно обновлено',
                'weight_category': weight_category,
                'is_valid': is_valid
            }), 200
        return jsonify({'message': 'Не получилось обновить данные взвешивания'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при обновлении взвешивания: {str(e)}'}), 500


@weighing_bp.route('/', methods=['POST'])
def create_weighing():
    """Создать запись о взвешивании"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Не передан JSON'}), 400

        if not data.get('tournament_id') or not data.get('athlete_id') or not data.get('weight'):
            return jsonify({'success': False, 'message': 'Обязательные поля: tournament_id, category_id, athlete_id, weight'}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            athlete_repo    = AthleteRepository(session)
            weighing_repo   = WeightRepository(session)

            tournament = tournament_repo.get_tournament_category(data['tournament_id'], data['category_id'])
            if not tournament:
                return jsonify({'success': False, 'message': 'Турнир не найден'}), 404

            athlete = athlete_repo.get_athlete_by_id(data['athlete_id'])
            if not athlete:
                return jsonify({'success': False, 'message': 'Участник не найден'}), 404

            # ✅ Передаём сессию в helper
            is_valid, correct_category_name = _is_valid_for_category(data, tournament, athlete, session)

            if not is_valid:
                message = (
                    f'Атлет не подходит для выбранной категории. Рекомендуемая категория: {correct_category_name}'
                    if correct_category_name
                    else 'Не удалось определить подходящую категорию для атлета'
                )
                return jsonify({'message': message}), 400

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_name(correct_category_name)

            # existing_weighting_repo = weighing_repo.get_existing_wight(tournament.tournament_category_id, athlete.id)

            weighing = WeighingNew(
                tournament_category_id=tournament.tournament_category_id,
                athlete_id=data['athlete_id'],
                weight=data['weight'],
                notes=data.get('notes'),
                weight_category=category.id if is_valid else athlete.category_id,
                is_valid=is_valid
            )
            is_added = weighing_repo.create_weighting(weighing)

            has_assign_tournament = tournament_repo.assign_athletes_tournament_after_weighting(tournament.tournament_category_id,athlete.id)

            if not is_added and not has_assign_tournament:
                return jsonify({'message': 'Ошибка создания взвешивания участника'}), 500

            # ✅ Читаем данные ВНУТРИ сессии
            weighing_id  = weighing.id
            weight_category = weighing.weight_category

        return jsonify({
            'success': True,
            'message': 'Взвешивание успешно записано',
            'weighing_id': weighing_id,
            'weight_category': weight_category,
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при создании записи взвешивания: {str(e)}'}), 500


@weighing_bp.route('/<int:tournament_id>/change-category', methods=['POST'])
def change_category(tournament_id):
    try:
        data = request.get_json()
        required = ['category_id', 'athlete_id']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'message': f'Не введены: {missing}'}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            athlete_repo = AthleteRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return jsonify({'message': 'Нет такого турнира'}), 404

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(data['category_id'])
            if not category:
                return jsonify({'message': 'Нет такой категории'}), 400

            tournament_category = tournament_repo.get_tournament_category(tournament.id, category.id)

            existing = session.query(AthleteRegistration.athlete_id).filter_by(
                tournament_category_id=tournament_category.tournament_category_id,
                athlete_id=data['athlete_id']
            ).first()

            # ✅ Читаем имя категории ВНУТРИ сессии
            category_name = category.name

            athlete = athlete_repo.get_athlete_by_id(data['athlete_id'])
            is_valid, correct_category_name = _is_valid_for_category(data, tournament, athlete, session)

            if existing and is_valid:
                return jsonify({'message': 'Участник находится в правильной категории'}), 200

            session.execute(
                update(AthleteRegistration)
                .where(AthleteRegistration.athlete_id == athlete.id, AthleteRegistration.tournament_category_id == tournament_category.tournament_category_id)
                .values(
                    athlete_id=data['athlete_id'],
                    tournament_category_id=tournament_category.tournament_category_id
                )
            )
            session.commit()

        return jsonify({'message': f'Участник перенесен в категорию {category_name}'}), 200

    except Exception as e:
        return jsonify({'message': f'Ошибка выполнения {e}'}), 500

@weighing_bp.route('<int:weight_id>', methods=['DELETE'])
def delete_weighing(weight_id):
    try:
        with WeightRepository() as weight_repo:
            is_deleted = weight_repo.delete_weighting(weight_id)
            if is_deleted:
                return jsonify({'success':True,'message':'Звешивание удаленно'})
    except Exception as e:
        return jsonify({'message': f'Ошибка выполнения {e}'}), 500

def _is_within_weight_category_limits(weighing: WeighingNew) -> bool:
    tc = weighing.tournament_categories
    if not tc or not tc.category:
        return False
    cat = tc.category
    if cat.min_weight is None or cat.max_weight is None:
        return False
    return cat.min_weight <= weighing.weight <= cat.max_weight


def _is_valid_for_category(data, tournament_category: TournamentCategory, athlete: AthleteNew, session):
    """Проверяет соответствие атлета категории. Использует переданную сессию."""
    tournament_repo = TournamentRepository(session)
    category_repo   = CategoryRepository(session)

    categories = tournament_repo.get_categories(tournament_category.tournament_id)
    if not categories:
        raise Exception('Нет категорий за турнир')

    matched_category_id = 0
    for category in categories:
        age_ok = category.min_year <= athlete.birth_date.year <= category.max_year
        gender_ok = category.gender.name == athlete.gender
        if not (age_ok and gender_ok):
            continue
        if category.max_weight and category.min_weight <= data['weight'] <= category.max_weight:
            matched_category_id = category.id
            break
        elif not category.max_weight and data['weight'] >= category.min_weight:
            matched_category_id = category.id
            break

    if matched_category_id == 0:
        raise Exception('Нет подходящей категории в турнире')

    category = category_repo.get_category_by_id(matched_category_id)
    if category is None:
        return (False, None)

    is_valid = data['category_id'] == matched_category_id
    return (is_valid, category.name)