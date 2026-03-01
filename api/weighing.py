from flask import Blueprint, request, jsonify
from sqlalchemy import update

from database.db import create_session
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
        athlete_id = request.args.get('athlete_id', type=int)
        category_id = request.args.get('category_id', type=int)

        if not category_id or not tournament_id:
            return jsonify({
                'success': False,
                'message': "Не веденны category_id, tournament_id"
            })

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_category(tournament_id, category_id)

            if not tournament:
                return jsonify({
                    'message':'Нет такого категории в турнире'
                })
            weighing_repo = WeightRepository(session)
            weighings = weighing_repo.get_weights(tournament.tournament_category_id,athlete_id)

            result = []
            athlete_repo = AthleteRepository(session)
            category_repo = CategoryRepository(session)
            for weighing in weighings:
                # Берём атлета по ID из текущего взвешивания
                athlete = athlete_repo.get_athlete_by_id(weighing.athlete_id)

                # Добавляем защиту от None
                athlete_name = None
                if athlete and athlete.user:
                    athlete_name = f'{athlete.user.first_name} {athlete.user.last_name} {athlete.user.middle_name or ""}'.strip()

                category = category_repo.get_category_by_id(weighing.weight_category)

                result.append({
                    'id': weighing.id,
                    'athlete_name': athlete_name or 'Атлет не найден',
                    'weight': weighing.weight,
                    'weight_category': {
                        'name': category.name,
                        'weight_range': f'от {category.min_weight} до {category.max_weight}',
                        'age-range': f'от {category.min_year} до {category.max_year}',
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
        with WeightRepository() as weighing_repo:
            weighing = weighing_repo.get_weight(weighing_id)
            if not weighing:
                return jsonify({
                    'success': False,
                    'message': 'Взвешивание не найдено'
                }), 404

            # Меняем статус на противоположный
            is_change = weighing_repo.change_weighing_validation(weighing_id)

        if is_change:
            return jsonify({
                'success': True,
                'message': f'Статус валидации изменен на {"валидно" if weighing.is_valid else "невалидно"}',
                'is_valid': weighing.is_valid,
                'status_display': _is_within_weight_category_limits(weighing)
            }), 200
        else:
            return jsonify({
                'message': 'Не получилось обновить статус'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при изменении статуса валидации: {str(e)}'
        }), 500

@weighing_bp.route('/<int:weighing_id>', methods=['PUT'])
def update_weighing(weighing_id):
    """Обновить запись о взвешивании"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'message': 'Нет данных для изменения'
            }),400

        with WeightRepository() as weighing_repo:
            weighing = weighing_repo.get_weight(weighing_id)

            if not weighing:
                return jsonify({
                    'success': False,
                    'message': 'Взвешивание не найдено'
                }), 404

            is_update = weighing_repo.update_weighing_information(weighing_id, data)
        if is_update:
            return jsonify({
                'success': True,
                'message': 'Взвешивание успешно обновлено',
                'weight_category': weighing.weight_category,
                'status': weighing.status_display,
                'is_valid': weighing.is_valid
            }), 200
        else:
            return jsonify({
                'message': 'Не получилось обновить данные для звешивания'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении взвешивания: {str(e)}'
        }), 500

@weighing_bp.route('/', methods=['POST'])
def create_weighing():
    """Создать запись о взвешивании"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('tournament_id') or  not data.get('category_id') or not data.get('athlete_id') or not data.get('weight'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: tournament_id, athlete_id, weight'
            }), 400

        # Проверяем существование турнира и участника
        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_category(data['tournament_id'], data['category_id'])
            athlete_repo = AthleteRepository()
            athlete = athlete_repo.get_athlete_by_id(data['athlete_id'])

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

            is_valid, correct_category_name = _is_valid_for_category(data, tournament,athlete)

            if not is_valid:
                if correct_category_name:
                    message = f'Атлет не подходит для выбранной категории. Рекомендуемая категория: {correct_category_name}'
                else:
                    message = 'Не удалось определить подходящую категорию для атлета'

                return jsonify({'message': message}), 400

            weighing = WeighingNew(
                tournament_category_id=tournament.tournament_category_id,  # Правильный ID
                athlete_id=data['athlete_id'],
                weight=data['weight'],
                notes=data.get('notes'),
                weight_category= data.get('category_id') if is_valid else athlete.category_id,
                is_valid = is_valid
            )
            weighing_repo = WeightRepository(session)
            is_added = weighing_repo.create_weighting(weighing)

            if not is_added:
                return jsonify({
                    'message': 'Ошибка создание звешивание участника'
                }), 500

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

@weighing_bp.route('/<int:tournament_id>/change-category', methods=['POST'])
def change_category(tournament_id):
    try:
        data = request.get_json()

        required = ['category_id', 'athlete_id']
        missing_fields = [field for field in required if field not in data]

        if missing_fields:
            return jsonify({
                'message': f'Не ввели {missing_fields}'
            }),400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return jsonify({
                    'message': 'Нет такого турнира'
                }), 404

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(data['category_id'])
            if not category:
                return jsonify({
                    'message': 'Нет такой категории'
                }),400

            tournament_category = tournament_repo.get_tournament_category(tournament.id,category.id)

            exesting_athlete = session.query(AthleteRegistration.athlete_id).filter_by(tournament_category_id=tournament_category.tournament_category_id,athlete_id=data['athlete_id']).first()
            if exesting_athlete:
                return jsonify({
                    'message':'Участник находится в правельной категории'
                }), 200
            else:
                updated_athlete = (
                    update(AthleteRegistration)
                    .values(athlete_id=data['athlete_id'],tournament_category_id=tournament_category.tournament_category_id,)
                )
                session.execute(updated_athlete)
                session.commit()

            return jsonify({
              'message': f'Участник перенесен в категорию {category.name}'
            }),200
    except Exception as e:
        return jsonify({
            'message': f'Ошибка выполнения {e}'
        }),500

def _is_within_weight_category_limits(weighing: WeighingNew) -> bool:
    tc = weighing.tournament_categories
    if not tc or not tc.category:
        return False   # или True — зависит от бизнес-логики

    cat = tc.category

    if cat.min_weight is None or cat.max_weight is None:
        return False   # категория некорректно настроена

    return cat.min_weight <= weighing.weight <= cat.max_weight

def _is_valid_for_category(data, tournament_category:TournamentCategory,athlete:AthleteNew):
    category_repo = CategoryRepository()

    # Получаем ID категории по параметрам спортсмена
    # category_id = category_repo.get_id_by_athlete_feature(
    #     data['weight'],
    #     athlete.birth_date.year,
    #     athlete.gender
    # )

    # Если категория не найдена
    # if category_id is None:
    #     return (False, None)

    with TournamentRepository() as tournament_repo:
        categories = tournament_repo.get_categories(tournament_category.tournament_id)

        if not categories:
            raise Exception('Нет категорий за турнир')

        category_has_in_tournament = 0
        for category in categories:
            if category.min_year <= athlete.birth_date.year <= category.max_year and category.gender.name == athlete.gender:
                if category.max_weight and category.min_weight <= data['weight'] <= category.max_weight:
                    category_has_in_tournament = category.id
                    break
                    # Открытая категория (больше X кг)
                elif not category.max_weight and data['weight'] >= category.min_weight:
                    category_has_in_tournament = category.id
                    break

        if category_has_in_tournament == 0:
            raise Exception('Нет подходящей категории в турнире')

        # Получаем объект категории
        category = category_repo.get_category_by_id(category_has_in_tournament)

        # Дополнительная проверка на случай если категория не найдена
        if category is None:
            return (False, None)

    # Проверяем соответствие
    is_valid = data['category_id'] == category_has_in_tournament

    return (is_valid, category.name)