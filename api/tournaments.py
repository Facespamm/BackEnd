from flask import Blueprint, request, jsonify
from flasgger import swag_from
from datetime import datetime

from flask_jwt_extended import jwt_required

from models.tournament import Tournament
from repository.tournament_repo import TournamentRepository

tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')


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

        query = Tournament.query
        if status:
            query = query.filter_by(status=status)

        tournaments = query.order_by(Tournament.start_date.desc()).all()

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
                'status': tournament.status,
                'tatami_count': tournament.tatami_count,
                'athletes_count': tournament.athletes_count,
                'progress_percentage': tournament.progress_percentage
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

        tournament = Tournament(
            name=data['name'],
            description=data.get('description'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            venue=data.get('venue'),
            city=data.get('city'),
            country=data.get('country', 'Россия'),
            tatami_count=data.get('tatami_count', 1)
        )

        if tournament.save_to_db():
            return jsonify({
                'id': tournament.id,
                'name': tournament.name,
                'start_date': tournament.start_date.isoformat(),
                'end_date': tournament.end_date.isoformat(),
                'status': tournament.status
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при создании турнира'
            }), 400

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Неверный формат даты: {str(e)}'
        }), 400
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
        tournament = Tournament.query.get(tournament_id)

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
            'status': tournament.status,
            'tatami_count': tournament.tatami_count,
            'athletes_count': tournament.athletes_count,
            'progress_percentage': tournament.progress_percentage
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
        tournament = Tournament.query.get(tournament_id)

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

        if tournament.save():
            return jsonify({
                'success': True,
                'message': 'Турнир успешно обновлен',
                'tournament': {
                    'id': tournament.id,
                    'name': tournament.name,
                    'status': tournament.status
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
        tournament = Tournament.query.get(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

        if tournament.delete():
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
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить категории турнира',
    'description': 'Возвращает список категорий конкретного турнира',
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
            'description': 'Список категорий',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'},
                        'gender': {'type': 'string'},
                        'min_weight': {'type': 'number'},
                        'max_weight': {'type': 'number'},
                        'min_age': {'type': 'integer'},
                        'max_age': {'type': 'integer'},
                        'athletes_count': {'type': 'integer'}
                    }
                }
            }
        },
        404: {
            'description': 'Турнир не найден'
        }
    }
})
def get_tournament_categories(tournament_id):
    """Получить категории турнира"""
    try:
        tournament = Tournament.query.get(tournament_id)

        if not tournament:
            return jsonify({
                'success': False,
                'message': 'Турнир не найден'
            }), 404

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
                'athletes_count': category.athletes_count
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


@tournaments_bp.route('/search-athlete', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Поиск участника по ФИО',
    'description': 'Поиск участника для получения его ID при регистрации на турнир',
    'parameters': [
        {
            'name': 'last_name',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Фамилия участника'
        },
        {
            'name': 'first_name',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Имя участника'
        },
        {
            'name': 'middle_name',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Отчество участника'
        },
        {
            'name': 'club_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'ID клуба для фильтрации'
        },
        {
            'name': 'is_active',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'description': 'Фильтр по активности участника',
            'default': True
        }
    ],
    'responses': {
        200: {
            'description': 'Список найденных участников',
            'schema': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'user_id': {'type': 'integer'},
                        'last_name': {'type': 'string'},
                        'first_name': {'type': 'string'},
                        'middle_name': {'type': 'string'},
                        'full_name': {'type': 'string'},
                        'birth_date': {'type': 'string', 'format': 'date'},
                        'age': {'type': 'integer'},
                        'gender': {'type': 'string'},
                        'club_id': {'type': 'integer'},
                        'club_name': {'type': 'string'},
                        'rank': {'type': 'string'},
                        'license_number': {'type': 'string'},
                        'is_active': {'type': 'boolean'}
                    }
                }
            }
        },
        400: {
            'description': 'Не указаны параметры поиска'
        }
    }
})
def search_athlete():
    """Поиск участника по ФИО для получения его ID"""
    try:
        from models.athlete import Athlete
        from models.user import User

        # Получаем параметры поиска
        last_name = request.args.get('last_name', '').strip()
        first_name = request.args.get('first_name', '').strip()
        middle_name = request.args.get('middle_name', '').strip()
        club_id = request.args.get('club_id')
        is_active = request.args.get('is_active', 'true').lower() == 'true'

        # Проверяем, что хотя бы один параметр передан
        if not any([last_name, first_name, middle_name, club_id]):
            return jsonify({
                'success': False,
                'message': 'Укажите хотя бы один параметр поиска (last_name, first_name, middle_name или club_id)'
            }), 400

        # Формируем запрос
        query = Athlete.query.filter_by(is_active=is_active)

        # Фильтр по клубу
        if club_id:
            try:
                query = query.filter_by(club_id=int(club_id))
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Неверный формат club_id'
                }), 400

        # Выполняем запрос и фильтруем по ФИО на уровне Python
        athletes = query.all()
        result = []

        for athlete in athletes:
            # Фильтрация по ФИО (частичное совпадение)
            matches = True

            if last_name and last_name.lower() not in (athlete.last_name or '').lower():
                matches = False
            if first_name and first_name.lower() not in (athlete.first_name or '').lower():
                matches = False
            if middle_name and middle_name.lower() not in (athlete.middle_name or '').lower():
                matches = False

            if matches:
                # Получаем имя ранга безопасно
                rank_display = None
                if athlete.rank:
                    # Проверяем, какие атрибуты есть у модели Dan
                    if hasattr(athlete.rank, 'name'):
                        rank_display = athlete.rank.name
                    elif hasattr(athlete.rank, 'title'):
                        rank_display = athlete.rank.title
                    elif hasattr(athlete.rank, 'level'):
                        rank_display = f"Дан {athlete.rank.level}"

                result.append({
                    'id': athlete.id,
                    'user_id': athlete.user_id,
                    'last_name': athlete.last_name,
                    'first_name': athlete.first_name,
                    'middle_name': athlete.middle_name,
                    'full_name': athlete.full_name,
                    'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                    'age': athlete.age,
                    'gender': athlete.gender,
                    'club_id': athlete.club_id,
                    'club_name': athlete.club.name if athlete.club else None,
                    'rank': rank_display,
                    'license_number': athlete.license_number,
                    'is_active': athlete.is_active
                })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при поиске участника: {str(e)}'
        }), 500


@tournaments_bp.route('/club-athletes', methods=['GET'])
@swag_from({
    'tags': ['Tournaments'],
    'summary': 'Получить всех участников клуба',
    'description': 'Возвращает список всех активных участников указанного клуба',
    'parameters': [
        {
            'name': 'club_id',
            'in': 'query',
            'type': 'integer',
            'required': True,
            'description': 'ID клуба'
        },
        {
            'name': 'only_active',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'description': 'Только активные участники',
            'default': True
        },
        {
            'name': 'include_tournament_info',
            'in': 'query',
            'type': 'boolean',
            'required': False,
            'description': 'Включить информацию о турнирах участника',
            'default': False
        },
        {
            'name': 'tournament_id',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'Фильтр по конкретному турниру'
        }
    ],
    'responses': {
        200: {
            'description': 'Список участников клуба',
            'schema': {
                'type': 'object',
                'properties': {
                    'club_id': {'type': 'integer'},
                    'club_name': {'type': 'string'},
                    'athletes_count': {'type': 'integer'},
                    'athletes': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'user_id': {'type': 'integer'},
                                'last_name': {'type': 'string'},
                                'first_name': {'type': 'string'},
                                'middle_name': {'type': 'string'},
                                'full_name': {'type': 'string'},
                                'birth_date': {'type': 'string', 'format': 'date'},
                                'age': {'type': 'integer'},
                                'gender': {'type': 'string'},
                                'rank': {'type': 'string'},
                                'license_number': {'type': 'string'},
                                'medical_check': {'type': 'boolean'},
                                'insurance_number': {'type': 'string'},
                                'is_active': {'type': 'boolean'},
                                'tournaments': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'tournament_id': {'type': 'integer'},
                                            'tournament_name': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Не указан club_id'
        },
        404: {
            'description': 'Клуб не найден'
        }
    }
})
def get_club_athletes():
    """Получить всех участников клуба"""
    try:
        from models.athlete import Athlete
        from models.club import Club

        # Получаем параметры
        club_id = request.args.get('club_id')
        only_active = request.args.get('only_active', 'true').lower() == 'true'
        include_tournament_info = request.args.get('include_tournament_info', 'false').lower() == 'true'
        tournament_id = request.args.get('tournament_id')

        if not club_id:
            return jsonify({
                'success': False,
                'message': 'Не указан club_id'
            }), 400

        # Проверяем существование клуба
        club = Club.query.get(club_id)
        if not club:
            return jsonify({
                'success': False,
                'message': f'Клуб с ID {club_id} не найден'
            }), 404

        # Формируем запрос
        query = Athlete.query.filter_by(club_id=club_id)

        if only_active:
            query = query.filter_by(is_active=True)

        # Фильтр по турниру
        if tournament_id:
            # Используем отношение tournament, которое определено в модели Athlete
            query = query.filter(Athlete.tournament.any(id=int(tournament_id)))

        athletes = query.all()

        # Формируем результат
        result = []
        for athlete in athletes:
            # Получаем имя ранга безопасно
            rank_display = None
            if athlete.rank:
                if hasattr(athlete.rank, 'name'):
                    rank_display = athlete.rank.name
                elif hasattr(athlete.rank, 'title'):
                    rank_display = athlete.rank.title
                elif hasattr(athlete.rank, 'level'):
                    rank_display = f"Дан {athlete.rank.level}"

            athlete_data = {
                'id': athlete.id,
                'user_id': athlete.user_id,
                'last_name': athlete.last_name,
                'first_name': athlete.first_name,
                'middle_name': athlete.middle_name,
                'full_name': athlete.full_name,
                'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                'age': athlete.age,
                'gender': athlete.gender,
                'rank': rank_display,
                'license_number': athlete.license_number,
                'medical_check': athlete.medical_check,
                'insurance_number': athlete.insurance_number,
                'is_active': athlete.is_active
            }

            # Добавляем информацию о турнирах
            if include_tournament_info:
                tournaments = []
                for tournament in athlete.tournament:
                    tournament_data = {
                        'tournament_id': tournament.id,
                        'tournament_name': tournament.name
                    }
                    tournaments.append(tournament_data)
                athlete_data['tournaments'] = tournaments

            result.append(athlete_data)

        return jsonify({
            'club_id': club.id,
            'club_name': club.name,
            'athletes_count': len(result),
            'athletes': result
        }), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'message': f'Неверный формат параметров: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участников клуба: {str(e)}'
        }), 500
@tournaments_bp.route('/<int:tournament_id>/add-athletes', methods=['POST'])
def add_athletes_to_tournament(tournament_id):
    """Добавить участников к турниру"""
    athlete_ids = request.get_json().get('athlete_ids')

    if not athlete_ids or not isinstance(athlete_ids, list):
        return jsonify({
            'success': False,
            'message': 'Не переданы участники или неверный формат'
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