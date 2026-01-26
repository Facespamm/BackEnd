from flask import Blueprint, jsonify
from flasgger import swag_from
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import distinct
from sqlalchemy.sql.functions import count

from new_model.handbook.role_new import RoleNew
from new_model.head_model.new_athlete import AthleteNew
from new_model.head_model.new_user import UserNew
from new_model.head_model.tournament_new import TournamentNew
from new_model.head_model.fight_new import FightNew
from new_model.new_associations import new_user_roles, AthleteRegistration, TournamentCategory
from new_model.Enums import StatusTournament, FightStatus
from database.db import db

statistics_bp = Blueprint('statistics', __name__, url_prefix='/statistics')



@statistics_bp.route('/live-overview', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Краткая статистика по активным турнирам (LIVE)',
    'responses': {
        200: {
            'description': 'Статистика успешно получена',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'active_tournaments': {'type': 'integer'},
                            'unique_athletes': {'type': 'integer'},
                            'live_fights': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_live_statistics():
    try:
        active_tournaments_count = (
            db.session.query(count(TournamentNew.id))
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_athletes_count = (
            db.session.query(count(distinct(AthleteRegistration.athlete_id)))
            .join(TournamentCategory, TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
            .join(TournamentNew, TournamentNew.id == TournamentCategory.tournament_id)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        live_fights_count = (
            db.session.query(count(FightNew.id))
            .join(TournamentNew)
            .filter(
                TournamentNew.status == StatusTournament.LIVE,
                FightNew.status == FightStatus.LIVE
            )
            .scalar() or 0
        )

        result = {
            'active_tournaments': active_tournaments_count,
            'unique_athletes': unique_athletes_count,
            'live_fights': live_fights_count
        }

        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@statistics_bp.route('/users', methods=['GET'])
@swag_from({
    'tags': ['Statistics', 'Users'],
    'summary': 'Получить список всех активных пользователей',
    'description': 'Возвращает список активных пользователей с основными данными и их ролями. '
                   'Пароль и служебные поля не возвращаются.',
    'responses': {
        200: {
            'description': 'Список пользователей получен',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'first_name': {'type': 'string'},
                                'last_name': {'type': 'string'},
                                'middle_name': {'type': 'string', 'nullable': True},
                                'email': {'type': 'string', 'nullable': True},
                                'phone': {'type': 'string', 'nullable': True},
                                'is_active': {'type': 'boolean'},
                                'roles': {
                                    'type': 'array',
                                    'items': {'type': 'string'}
                                }
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_all_users():
    """
    Получить список всех активных пользователей с их ролями
    """
    try:
        # Загружаем всех активных пользователей с предзагрузкой ролей
        users = (
            db.session.query(UserNew)
            .filter(UserNew.is_active == True)
            .options(joinedload(UserNew.roles))
            .order_by(UserNew.last_name, UserNew.first_name)
            .all()
        )

        result = []
        for user in users:
            # Собираем список названий ролей
            user_roles = [role.name for role in user.roles]

            result.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'middle_name': user.middle_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'roles': user_roles
            })

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении списка пользователей: {str(e)}'
        }), 500

@statistics_bp.route('/live-detailed', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Расширенная статистика по активным турнирам (LIVE)',
    'responses': {
        200: {
            'description': 'Статистика успешно получена',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'active_tournaments': {'type': 'integer'},
                            'unique_athletes': {'type': 'integer'},
                            'unique_clubs': {'type': 'integer'},
                            'total_users': {'type': 'integer'},
                            'live_fights': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_live_detailed_statistics():
    try:
        active_tournaments_count = (
            db.session.query(count(TournamentNew.id))
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_athletes_count = (
            db.session.query(count(distinct(AthleteRegistration.athlete_id)))
            .join(TournamentCategory, TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
            .join(TournamentNew, TournamentNew.id == TournamentCategory.tournament_id)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_clubs_count = (
            db.session.query(count(distinct(AthleteNew.club_id)))
            .join(AthleteRegistration, AthleteRegistration.athlete_id == AthleteNew.id)
            .join(TournamentCategory, TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
            .join(TournamentNew, TournamentCategory.tournament_id == TournamentNew.id)
            .filter(
                TournamentNew.status == StatusTournament.LIVE,
                AthleteNew.club_id.isnot(None)
            )
            .scalar() or 0
        )

        total_users_count = (
            db.session.query(count(UserNew.id))
            .filter(UserNew.is_active == True)
            .scalar() or 0
        )

        live_fights_count = (
            db.session.query(count(FightNew.id))
            .join(TournamentNew)
            .filter(
                TournamentNew.status == StatusTournament.LIVE,
                FightNew.status == FightStatus.LIVE
            )
            .scalar() or 0
        )

        result = {
            'active_tournaments': active_tournaments_count,
            'unique_athletes': unique_athletes_count,
            'unique_clubs': unique_clubs_count,
            'total_users': total_users_count,
            'live_fights': live_fights_count
        }

        return jsonify({'success': True, 'data': result}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'}), 500

@statistics_bp.route('/users-by-role', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Статистика пользователей по ролям',
    'description': 'Возвращает общее количество активных пользователей и распределение по ролям',
    'responses': {
        200: {
            'description': 'Статистика успешно получена',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'total_active_users': {'type': 'integer'},
                            'users_by_role': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'role_name': {'type': 'string'},
                                        'normalized_name': {'type': 'string'},
                                        'count': {'type': 'integer'}
                                    }
                                }
                            },
                            'users_without_role': {'type': 'integer'}
                        }
                    }
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_users_by_role_statistics():
    """
    Получить статистику пользователей по ролям
    """
    try:
        # 1. Общее количество активных пользователей
        total_active_users = (
            db.session.query(count(UserNew.id))
            .filter(UserNew.is_active == True)
            .scalar() or 0
        )

        # 2. Количество пользователей по каждой роли
        users_by_role = (
            db.session.query(
                RoleNew.name.label('role_name'),
                RoleNew.normalized_name.label('normalized_name'),
                count(UserNew.id).label('count')
            )
            .join(new_user_roles, RoleNew.id == new_user_roles.c.role_id)
            .join(UserNew, UserNew.id == new_user_roles.c.user_id)
            .filter(UserNew.is_active == True)
            .group_by(RoleNew.id, RoleNew.name, RoleNew.normalized_name)
            .order_by(RoleNew.name)
            .all()
        )

        # 3. Пользователи без ролей (активные)
        users_without_role = (
            db.session.query(count(UserNew.id))
            .outerjoin(new_user_roles, UserNew.id == new_user_roles.c.user_id)
            .filter(
                UserNew.is_active == True,
                new_user_roles.c.user_id.is_(None)
            )
            .scalar() or 0
        )

        # Формируем список ролей
        role_list = [
            {
                'role_name': role.role_name,
                'normalized_name': role.normalized_name,
                'count': role.count
            }
            for role in users_by_role
        ]

        result = {
            'total_active_users': total_active_users,
            'users_by_role': role_list,
            'users_without_role': users_without_role
        }

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении статистики пользователей: {str(e)}'
        }), 500
@statistics_bp.route('/active-tournaments', methods=['GET'])
@swag_from({
    'tags': ['Statistics'],
    'summary': 'Список всех активных турниров (статус LIVE)',
    'description': 'Возвращает список турниров со статусом LIVE с основной информацией',
    'responses': {
        200: {
            'description': 'Список турниров получен',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'start_date': {'type': 'string'},
                                'end_date': {'type': 'string'},
                                'city': {'type': 'string'},
                                'country': {'type': 'string'},
                                'tatami_count': {'type': 'integer'},
                                'athletes_count': {'type': 'integer'},
                                'live_fights_count': {'type': 'integer'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {'description': 'Ошибка сервера'}
    }
})
def get_active_tournaments():
    """
    Получить список всех турниров со статусом LIVE
    """
    try:
        # Получаем все активные турниры с предзагрузкой связей
        tournaments = (
            db.session.query(TournamentNew)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .options(joinedload(TournamentNew.athletes))
            .all()
        )

        result = []
        for tournament in tournaments:
            # Количество уникальных атлетов на турнире
            athletes_count = (
                db.session.query(count(distinct(AthleteRegistration.athlete_id)))
                .join(TournamentCategory, TournamentCategory.tournament_category_id == AthleteRegistration.tournament_category_id)
                .filter(TournamentCategory.tournament_id == tournament.id)
                .scalar() or 0
            )

            # Количество активных боёв на этом турнире
            live_fights_count = (
                db.session.query(count(FightNew.id))
                .filter(
                    FightNew.tournament_id == tournament.id,
                    FightNew.status == FightStatus.LIVE
                )
                .scalar() or 0
            )

            result.append({
                'id': tournament.id,
                'name': tournament.name,
                'start_date': tournament.start_date.isoformat() if tournament.start_date else None,
                'end_date': tournament.end_date.isoformat() if tournament.end_date else None,
                'city': tournament.city,
                'country': tournament.country,
                'tatami_count': tournament.tatami_count,
                'athletes_count': athletes_count,
                'live_fights_count': live_fights_count
            })

        return jsonify({
            'success': True,
            'data': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении списка турниров: {str(e)}'
        }), 500

