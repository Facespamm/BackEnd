from flask import Blueprint, jsonify
from flasgger import swag_from
from sqlalchemy import func, distinct
from sqlalchemy.orm import joinedload

# Ваши импорты (как указано)
from new_model.head_model.tournament_new import TournamentNew
from new_model.head_model.fight_new import FightNew
from new_model.handbook import new_club
from new_model.head_model import new_athlete
from new_model.head_model import new_user
from new_model.new_associations import athlete_tournament

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
            db.session.query(func.count(TournamentNew.id))
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_athletes_count = (
            db.session.query(func.count(distinct(athlete_tournament.c.athlete_id)))
            .join(TournamentNew, TournamentNew.id == athlete_tournament.c.tournament_id)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        live_fights_count = (
            db.session.query(func.count(FightNew.id))
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
            db.session.query(func.count(TournamentNew.id))
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_athletes_count = (
            db.session.query(func.count(distinct(athlete_tournament.c.athlete_id)))
            .join(TournamentNew, TournamentNew.id == athlete_tournament.c.tournament_id)
            .filter(TournamentNew.status == StatusTournament.LIVE)
            .scalar() or 0
        )

        unique_clubs_count = (
            db.session.query(func.count(distinct(new_athlete.AthleteNew.club_id)))
            .join(athlete_tournament, new_athlete.AthleteNew.id == athlete_tournament.c.athlete_id)
            .join(TournamentNew, TournamentNew.id == athlete_tournament.c.tournament_id)
            .filter(
                TournamentNew.status == StatusTournament.LIVE,
                new_athlete.AthleteNew.club_id.isnot(None)
            )
            .scalar() or 0
        )

        total_users_count = (
            db.session.query(func.count(new_user.UserNew.id))
            .filter(new_user.UserNew.is_active == True)
            .scalar() or 0
        )

        live_fights_count = (
            db.session.query(func.count(FightNew.id))
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
                db.session.query(func.count(distinct(athlete_tournament.c.athlete_id)))
                .filter(athlete_tournament.c.tournament_id == tournament.id)
                .scalar() or 0
            )

            # Количество активных боёв на этом турнире
            live_fights_count = (
                db.session.query(func.count(FightNew.id))
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