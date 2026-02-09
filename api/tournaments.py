from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime

from new_model.head_model.tournament_new import TournamentNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.handbook.category_new import CategoryNew
from new_model.new_associations import TournamentCategory, AthleteRegistration
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository
from sqlalchemy.orm import joinedload
tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/api/tournaments')
tournament_repo = TournamentRepository()

@tournaments_bp.route('/', methods=['GET'])
def get_tournaments():
    """Получить список всех турниров"""
    try:
        status = request.args.get('status')

        tournaments = tournament_repo.get_all_tournaments(status)

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
                'status': tournament.status.value,
                'tatami_count': tournament.tatami_count,
                'athletes_count': tournament_repo.get_athlete_count(tournament.id)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении турниров: {str(e)}'
        }), 500

@tournaments_bp.route('/', methods=['POST'])
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

        if not data.get('list_category'):
            return jsonify({
                'success': False,
                'message': 'Нет категорий'
            }),400

        tournament_new = TournamentNew(
            name=data['name'],
            description=data.get('description'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            venue=data.get('venue'),
            city=data.get('city'),
            country=data.get('country', 'Россия'),
            tatami_count=data.get('tatami_count', 1),
            has_consolation_fights = data.get('has_consalation',False)
        )

        is_created = tournament_repo.create_tournament(tournament_new)

        for category in data['list_category']:
            tournament_repo.assign_category_tournament(category, tournament_new.id, data.get('has_consalation',False))

        if not is_created:
            return jsonify({
                'message':'Ошибка создание турнира',
                'success': False
            }),400
        else:
            return jsonify({
                'id': tournament_new.id,
                'name': tournament_new.name,
                'start_date': tournament_new.start_date.isoformat(),
                'end_date': tournament_new.end_date.isoformat(),
                'status': tournament_new.status.value
            }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании турнира: {str(e)}'
        }), 500

@tournaments_bp.route('/by-category/<int:category_id>', methods=['GET'])
def get_tournaments_by_category(category_id):
    """
    Получить список турниров по указанной категории
    ---
    Параметры:
        category_id (path): ID категории
        status (query, optional): фильтр по статусу турнира (строковое значение enum, например, PLANNED, ACTIVE и т.д.)
    """
    try:
        status = request.args.get('status')  # Опциональный фильтр по статусу (строка, как в основном эндпоинте)

        query = TournamentNew.query.filter(
            TournamentNew.tournament_categories.any(category_id=category_id)
        )

        if status:
            # Предполагается, что status передаётся как строковое значение enum (например, 'PLANNED')
            query = query.filter(TournamentNew.status == status)

        # Сортировка по дате начала (сначала ближайшие)
        query = query.order_by(TournamentNew.start_date.desc())

        tournaments = query.all()

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
                'status': tournament.status.value if tournament.status else None,
                'tatami_count': tournament.tatami_count,
                'athletes_count': tournament_repo.get_athlete_count(tournament.id)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении турниров по категории: {str(e)}'
        }), 500

@tournaments_bp.route('/<int:tournament_id>', methods=['GET'])
def get_tournament(tournament_id):
    """Получить информацию о турнире"""
    try:
        tournament = tournament_repo.get_tournament_by_id(tournament_id)

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
            'status': tournament.status.value,
            'tatami_count': tournament.tatami_count,
            'athletes_count': tournament_repo.get_athlete_count(tournament.id),
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении турнира: {str(e)}'
        }), 500

@tournaments_bp.route('/<int:tournament_id>', methods=['PUT'])
def update_tournament(tournament_id):
    """Обновить информацию о турнире"""
    try:
        tournament = tournament_repo.get_tournament_by_id(tournament_id)

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

        if tournament_repo.commit_change():
            return jsonify({
                'success': True,
                'message': 'Турнир успешно обновлен',
                'tournament': {
                    'id': tournament.id,
                    'name': tournament.name,
                    'status': tournament.status.value
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
def delete_tournament(tournament_id):
    """Удалить турнир"""
    try:
        tournament = tournament_repo.get_tournament_by_id(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        if tournament_repo.delete_tournament(tournament):
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
def get_tournament_categories(tournament_id):
    """Получить категории турнира"""
    try:
        tournament = tournament_repo.get_tournament_by_id(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        category_repo = CategoryRepository()
        result = []
        for tournament_category in tournament.tournament_categories:
            category = tournament_category.category
            result.append({
                'id': category.id,
                'name': category.name,
                'gender': category.gender.value,
                'min_weight': category.min_weight,
                'max_weight': category.max_weight,
                'min_age': category.min_year,
                'max_age': category.max_year,
                'athletes_count': category_repo.get_all_athletes(category.id)
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении категорий: {str(e)}'
        }), 500

@tournaments_bp.route('/<int:tournament_id>/add-club',  methods=['POST'])
def add_club_to_tournament(tournament_id):
    """Добавить клуб к турниру"""
    club_id =request.args.get('club_id')

    if not club_id:
        return jsonify({
            'success': False,
            'message': 'Не передан клуб'
        }), 400

    if not tournament_id:
        return jsonify({
            'success': False,

            'message': 'Не передан турнир'
        }), 400

    tournament= TournamentRepository()
    try:
        is_added = tournament.add_club_to_tournament(tournament_id, club_id)

        if not is_added:
            return jsonify({
                'message': 'Не получилось добавить клуб к турниру'
            }), 500

        return jsonify({
            'success': True,
            'message': f'Клуб {club_id} добавлен к турниру {tournament_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при добавлении клуба к турниру: {str(e)}'
        }), 500


@tournaments_bp.route('/<int:tournament_id>/athletes', methods=['GET'])
def get_tournament_athletes(tournament_id):
    """Получить список зарегистрированных атлетов на турнир"""
    try:
        tournament = tournament_repo.get_tournament_by_id(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        # Опциональная фильтрация по категории
        category_id = request.args.get('category_id', type=int)

        athletes = tournament_repo.get_tournament_athletes(tournament_id, category_id)

        result = []
        for athlete_data in athletes:
            athlete = athlete_data['athlete']
            category = athlete_data['category']

            result.append({
                'athlete_id': athlete.id,
                'first_name': athlete.user.first_name if athlete.user else None,
                'last_name': athlete.user.last_name if athlete.user else None,
                'gender': athlete.gender,
                'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                'age': athlete.age,
                'club_name': athlete.club.name if athlete.club else None,
                'rank': athlete.rank.level if athlete.rank else None,  # Используем level вместо name
                'category_id': category.id,
                'category_name': category.name
            })

        return jsonify({
            'success': True,
            'tournament_id': tournament_id,
            'athletes_count': len(result),
            'athletes': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении атлетов турнира: {str(e)}'
        }), 500
@tournaments_bp.route('/<int:tournament_id>/add-athletes', methods=['POST'])
def add_athletes_to_tournament(tournament_id):
    """Добавить участников к турниру"""
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': 'Не переданы участники и категория'
        }),400

    athlete_ids = data.get('athlete_ids')
    category_id = data.get('category_id')

    if not athlete_ids or not isinstance(athlete_ids, list):
        return jsonify({
            'success': False,
            'message': 'Не переданы участники или неверный формат'
        }), 400

    if not category_id:
        return jsonify({
            'success': False,
            'message': 'Не передана категория'
        }), 400

    if not tournament_id:
        return jsonify({
            'success': False,
            'message': 'Не передан турнир'
        }), 400

    tournament = TournamentRepository()
    try:
        added_athletes = 0
        for athlete_id in athlete_ids:
            is_add = tournament.add_athlete_to_tournament(tournament_id, category_id,athlete_id)
            if is_add:
                added_athletes += 1

        return jsonify({
            'success': True,
            'message': f'Участники добавлены к турниру {tournament_id}',
            'count_added': added_athletes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при добавлении участников к турниру: {str(e)}'
        }), 500