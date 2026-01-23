from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime

from new_model.head_model.tournament_new import TournamentNew
from repository.category_repo import CategoryRepository
from repository.tournament_repo import TournamentRepository

tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')
tournament_repo = TournamentRepository()

@tournaments_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить список всех турниров',
    'description': 'Возвращает список турниров с возможностью фильтрации по статусу',
    'parameters': [
        {
            'name': 'status',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Статус турнира для фильтрации',
            'enum': ['DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED']
        }
    ],
    'responses': {
        200: {
            'description': 'Список турниров получен успешно',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'start_date': {'type': 'string', 'format': 'date'},
                        'end_date': {'type': 'string', 'format': 'date'},
                        'venue': {'type': 'string'},
                        'city': {'type': 'string'},
                        'country': {'type': 'string'},
                        'status': {'type': 'string'},
                        'tatami_count': {'type': 'integer'},
                        'athletes_count': {'type': 'integer'},
                        'progress_percentage': {'type': 'integer'}
                    }
                }
            }
        }
    }
})
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
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Создать новый турнир',
    'description': 'Создает новый турнир в системе',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['name', 'start_date', 'end_date'],
                'properties': {
                    'name': {'type': 'string', 'description': 'Название турнира'},
                    'description': {'type': 'string', 'description': 'Описание турнира'},
                    'start_date': {'type': 'string', 'format': 'date', 'description': 'Дата начала (ISO формат)'},
                    'end_date': {'type': 'string', 'format': 'date', 'description': 'Дата окончания (ISO формат)'},
                    'venue': {'type': 'string', 'description': 'Место проведения'},
                    'city': {'type': 'string', 'description': 'Город'},
                    'country': {'type': 'string', 'description': 'Страна', 'default': 'Россия'},
                    'tatami_count': {'type': 'integer', 'description': 'Количество татами', 'default': 1}
                }
            }
        }
    ],
    'responses': {
        201: {
            'description': 'Турнир успешно создан',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'start_date': {'type': 'string'},
                    'end_date': {'type': 'string'},
                    'status': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Ошибка валидации'
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
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
            tatami_count=data.get('tatami_count', 1)
        )

        is_created = tournament_repo.create_tournament(tournament_new)

        for category in data['list_category']:
            tournament_repo.assign_category_tournament(category, tournament_new.id)

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
                'status': tournament_new.status
            }), 201
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании турнира: {str(e)}'
        }), 500

@tournaments_bp.route('/<int:tournament_id>', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить информацию о турнире',
    'description': 'Возвращает детальную информацию о конкретном турнире',
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
            'description': 'Информация о турнире',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'start_date': {'type': 'string'},
                    'end_date': {'type': 'string'},
                    'venue': {'type': 'string'},
                    'city': {'type': 'string'},
                    'country': {'type': 'string'},
                    'status': {'type': 'string'},
                    'tatami_count': {'type': 'integer'},
                    'athletes_count': {'type': 'integer'},
                    'progress_percentage': {'type': 'integer'}
                }
            }
        },
        404: {
            'description': 'Турнир не найден'
        }
    }
})
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
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Обновить информацию о турнире',
    'description': 'Обновляет данные турнира',
    'parameters': [
        {
            'name': 'tournament_id',
            'in': 'path',
            'type': 'integer',
            'required': True,
            'description': 'ID турнира'
        },
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'description': {'type': 'string'},
                    'start_date': {'type': 'string', 'format': 'date'},
                    'end_date': {'type': 'string', 'format': 'date'},
                    'venue': {'type': 'string'},
                    'city': {'type': 'string'},
                    'country': {'type': 'string'},
                    'status': {'type': 'string'},
                    'tatami_count': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Турнир успешно обновлен'
        },
        404: {
            'description': 'Турнир не найден'
        },
        400: {
            'description': 'Ошибка при обновлении'
        }
    }
})
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
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Удалить турнир',
    'description': 'Удаляет турнир из системы',
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
            'description': 'Турнир успешно удален'
        },
        404: {
            'description': 'Турнир не найден'
        },
        400: {
            'description': 'Ошибка при удалении'
        }
    }
})
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
        for category in tournament.categories:
            result.append({
                'id': category.id,
                'name': category.name,
                'gender': category.gender,
                'min_weight': category.min_weight,
                'max_weight': category.max_weight,
                'min_age': category.min_age,
                'max_age': category.max_age,
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
    club_id =request.get('club_id')

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
        tournament.add_club_to_tournament(tournament_id, club_id)
        return jsonify({
            'success': True,
            'message': f'Клуб {club_id} добавлен к турниру {tournament_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при добавлении клуба к турниру: {str(e)}'
        }), 500

# TODO перенести в api/athletes.py
# @tournaments_bp.route('/search-athlete', methods=['GET'])
# def search_athlete():
#     """Поиск участника по ФИО для получения его ID"""
#     try:
#         from models.athlete import Athlete
#         from models.user import User
#
#         # Получаем параметры поиска
#         last_name = request.args.get('last_name', '').strip()
#         first_name = request.args.get('first_name', '').strip()
#         middle_name = request.args.get('middle_name', '').strip()
#         club_id = request.args.get('club_id')
#         is_active = request.args.get('is_active', 'true').lower() == 'true'
#
#         # Проверяем, что хотя бы один параметр передан
#         if not any([last_name, first_name, middle_name, club_id]):
#             return jsonify({
#                 'success': False,
#                 'message': 'Укажите хотя бы один параметр поиска (last_name, first_name, middle_name или club_id)'
#             }), 400
#
#         # Формируем запрос
#         query = Athlete.query.filter_by(is_active=is_active)
#
#         # Фильтр по клубу
#         if club_id:
#             try:
#                 query = query.filter_by(club_id=int(club_id))
#             except ValueError:
#                 return jsonify({
#                     'success': False,
#                     'message': 'Неверный формат club_id'
#                 }), 400
#
#         # Выполняем запрос и фильтруем по ФИО на уровне Python
#         athletes = query.all()
#         result = []
#
#         for athlete in athletes:
#             # Фильтрация по ФИО (частичное совпадение)
#             matches = True
#
#             if last_name and last_name.lower() not in (athlete.last_name or '').lower():
#                 matches = False
#             if first_name and first_name.lower() not in (athlete.first_name or '').lower():
#                 matches = False
#             if middle_name and middle_name.lower() not in (athlete.middle_name or '').lower():
#                 matches = False
#
#             if matches:
#                 # Получаем имя ранга безопасно
#                 rank_display = None
#                 if athlete.rank:
#                     # Проверяем, какие атрибуты есть у модели Dan
#                     if hasattr(athlete.rank, 'name'):
#                         rank_display = athlete.rank.name
#                     elif hasattr(athlete.rank, 'title'):
#                         rank_display = athlete.rank.title
#                     elif hasattr(athlete.rank, 'level'):
#                         rank_display = f"Дан {athlete.rank.level}"
#
#                 result.append({
#                     'id': athlete.id,
#                     'user_id': athlete.user_id,
#                     'last_name': athlete.last_name,
#                     'first_name': athlete.first_name,
#                     'middle_name': athlete.middle_name,
#                     'full_name': athlete.full_name,
#                     'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
#                     'age': athlete.age,
#                     'gender': athlete.gender,
#                     'club_id': athlete.club_id,
#                     'club_name': athlete.club.name if athlete.club else None,
#                     'rank': rank_display,
#                     'license_number': athlete.license_number,
#                     'is_active': athlete.is_active
#                 })
#
#         return jsonify(result), 200
#
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'message': f'Ошибка при поиске участника: {str(e)}'
#         }), 500

# # TODO переместить в api/club.py
# @tournaments_bp.route('/club-athletes', methods=['GET'])
# def get_club_athletes():
#     """Получить всех участников клуба"""
#     try:
#         from models.athlete import Athlete
#         from models.club import Club
#
#         # Получаем параметры
#         club_id = request.args.get('club_id')
#         only_active = request.args.get('only_active', 'true').lower() == 'true'
#         include_tournament_info = request.args.get('include_tournament_info', 'false').lower() == 'true'
#         tournament_id = request.args.get('tournament_id')
#
#         if not club_id:
#             return jsonify({
#                 'success': False,
#                 'message': 'Не указан club_id'
#             }), 400
#
#         # Проверяем существование клуба
#         club = Club.query.get(club_id)
#         if not club:
#             return jsonify({
#                 'success': False,
#                 'message': f'Клуб с ID {club_id} не найден'
#             }), 404
#
#         # Формируем запрос
#         query = Athlete.query.filter_by(club_id=club_id)
#
#         if only_active:
#             query = query.filter_by(is_active=True)
#
#         # Фильтр по турниру
#         if tournament_id:
#             # Используем отношение tournament, которое определено в модели Athlete
#             query = query.filter(Athlete.tournament.any(id=int(tournament_id)))
#
#         athletes = query.all()
#
#         # Формируем результат
#         result = []
#         for athlete in athletes:
#             # Получаем имя ранга безопасно
#             rank_display = None
#             if athlete.rank:
#                 if hasattr(athlete.rank, 'name'):
#                     rank_display = athlete.rank.name
#                 elif hasattr(athlete.rank, 'title'):
#                     rank_display = athlete.rank.title
#                 elif hasattr(athlete.rank, 'level'):
#                     rank_display = f"Дан {athlete.rank.level}"
#
#             athlete_data = {
#                 'id': athlete.id,
#                 'user_id': athlete.user_id,
#                 'last_name': athlete.last_name,
#                 'first_name': athlete.first_name,
#                 'middle_name': athlete.middle_name,
#                 'full_name': athlete.full_name,
#                 'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
#                 'age': athlete.age,
#                 'gender': athlete.gender,
#                 'rank': rank_display,
#                 'license_number': athlete.license_number,
#                 'medical_check': athlete.medical_check,
#                 'insurance_number': athlete.insurance_number,
#                 'is_active': athlete.is_active
#             }
#
#             # Добавляем информацию о турнирах
#             if include_tournament_info:
#                 tournaments = []
#                 for tournament in athlete.tournament:
#                     tournament_data = {
#                         'tournament_id': tournament.id,
#                         'tournament_name': tournament.name
#                     }
#                     tournaments.append(tournament_data)
#                 athlete_data['tournaments'] = tournaments
#
#             result.append(athlete_data)
#
#         return jsonify({
#             'club_id': club.id,
#             'club_name': club.name,
#             'athletes_count': len(result),
#             'athletes': result
#         }), 200
#
#     except ValueError as e:
#         return jsonify({
#             'success': False,
#             'message': f'Неверный формат параметров: {str(e)}'
#         }), 400
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'message': f'Ошибка при получении участников клуба: {str(e)}'
#         }), 500
#

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
        for athlete_id in athlete_ids:
            tournament.add_athlete_to_tournament(tournament_id, athlete_id)

        return jsonify({
            'success': True,
            'message': f'Участники добавлены к турниру {tournament_id}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при добавлении участников к турниру: {str(e)}'
        }), 500