from fastapi import APIRouter
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import distinct
from sqlalchemy.sql.functions import count

from database.db import create_session
from models import AthleteTournamentRegistration
from models.Enums import FightStatus, StatusTournament
from models.fight_new import FightNew
from models.new_associations import (
    AthleteRegistration,
    TournamentCategory,
    new_user_roles,
)
from models.new_user import UserNew
from models.role_new import RoleNew
from models.tournament_new import TournamentNew
from routers.statistic.schemas import (
    ActiveTournamentDTO,
    LiveStatisticsDTO,
    StatisticUserDTO,
    UpdatedUserDTO,
    UpdateStatisticUserRequest,
    UsersByRoleDTO,
    UsersRoleStatisticsDTO,
)
from utils.helpers import error_response

statistics_router = APIRouter(prefix="/api/statistics", tags=["Statistics"])


@statistics_router.get("/live-overview")
def get_live_statistics():
    try:
        with create_session() as session:
            active_tournaments_count = (
                session.query(count(TournamentNew.id))
                .filter(
                    TournamentNew.status == StatusTournament.LIVE,
                    TournamentNew.is_active == True,
                )
                .scalar()
                or 0
            )

            unique_athletes_count = (
                session.query(count(distinct(AthleteRegistration.athlete_id)))
                .join(
                    TournamentCategory,
                    TournamentCategory.tournament_category_id
                    == AthleteRegistration.tournament_category_id,
                )
                .join(
                    TournamentNew,
                    TournamentNew.id == TournamentCategory.tournament_id,
                )
                .filter(TournamentNew.status == StatusTournament.LIVE)
                .scalar()
                or 0
            )

            live_fights_count = (
                session.query(count(FightNew.id))
                .join(
                    TournamentCategory,
                    TournamentCategory.tournament_category_id
                    == FightNew.tournament_category_id,
                )
                .join(
                    TournamentNew,
                    TournamentCategory.tournament_id == TournamentNew.id,
                )
                .filter(
                    TournamentNew.status == StatusTournament.LIVE,
                    FightNew.status == FightStatus.LIVE,
                )
                .scalar()
                or 0
            )

        data = LiveStatisticsDTO(
            active_tournaments=active_tournaments_count,
            unique_athletes=unique_athletes_count,
            live_fights=live_fights_count,
        )
        return {"success": True, "data": data.model_dump()}

    except Exception as e:
        return error_response(f"Ошибка: {str(e)}", 500)


@statistics_router.get("/users")
def get_all_users():
    """Получить список всех активных пользователей с их ролями"""
    try:
        with create_session() as session:
            users = (
                session.query(UserNew)
                .filter(UserNew.is_active == True)
                .options(joinedload(UserNew.roles))
                .order_by(UserNew.last_name, UserNew.first_name)
                .all()
            )
            result = [StatisticUserDTO.from_user(user).model_dump() for user in users]

        return {"success": True, "data": result, "total": len(result)}

    except Exception as e:
        return error_response(
            f"Ошибка при получении списка пользователей: {str(e)}", 500
        )


@statistics_router.delete("/users/{user_id}")
def delete_user(user_id: int):
    try:
        with create_session() as session:
            user = session.query(UserNew).filter(UserNew.id == user_id).first()
            if not user:
                return error_response(f"Пользователь с ID {user_id} не найден", 404)

            username = user.username
            session.delete(user)
            session.commit()

        return {"success": True, "message": f"Пользователь {username} успешно удалён"}

    except Exception as e:
        return error_response(f"Ошибка при удалении пользователя: {str(e)}", 500)


@statistics_router.put("/users/{user_id}")
def update_user(user_id: int, data: UpdateStatisticUserRequest):
    try:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return error_response("Не переданы данные для обновления", 400)

        with create_session() as session:
            user = session.query(UserNew).filter(UserNew.id == user_id).first()
            if not user:
                return error_response(f"Пользователь с ID {user_id} не найден", 404)

            for field, value in update_data.items():
                setattr(user, field, value)

            session.commit()
            user_data = UpdatedUserDTO.from_user(user).model_dump()

        return {
            "success": True,
            "message": "Пользователь успешно обновлён",
            "user": user_data,
        }

    except Exception as e:
        return error_response(f"Ошибка при обновлении пользователя: {str(e)}", 500)


@statistics_router.get("/users-by-role")
def get_users_by_role_statistics():
    """Получить статистику пользователей по ролям"""
    try:
        with create_session() as session:
            total_active_users = (
                session.query(count(UserNew.id))
                .filter(UserNew.is_active == True)
                .scalar()
                or 0
            )

            users_by_role = (
                session.query(
                    RoleNew.name.label("role_name"),
                    RoleNew.normalized_name.label("normalized_name"),
                    count(UserNew.id).label("count_user_role"),
                )
                .join(new_user_roles, RoleNew.id == new_user_roles.c.role_id)
                .join(UserNew, UserNew.id == new_user_roles.c.user_id)
                .filter(UserNew.is_active == True)
                .group_by(RoleNew.id, RoleNew.name, RoleNew.normalized_name)
                .order_by(RoleNew.name)
                .all()
            )

            users_without_role = (
                session.query(count(UserNew.id))
                .outerjoin(new_user_roles, UserNew.id == new_user_roles.c.user_id)
                .filter(
                    UserNew.is_active == True,
                    new_user_roles.c.user_id.is_(None),
                )
                .scalar()
                or 0
            )

        data = UsersRoleStatisticsDTO(
            total_active_users=total_active_users,
            users_by_role=[
                UsersByRoleDTO(
                    role_name=role.role_name,
                    normalized_name=role.normalized_name,
                    count=role.count_user_role,
                )
                for role in users_by_role
            ],
            users_without_role=users_without_role,
        )

        return {"success": True, "data": data.model_dump()}

    except Exception as e:
        return error_response(
            f"Ошибка при получении статистики пользователей: {str(e)}",
            500,
        )


@statistics_router.get("/active-tournaments")
def get_active_tournaments():
    """Получить список всех турниров со статусом LIVE"""
    try:
        with create_session() as session:
            tournaments = (
                session.query(TournamentNew)
                .filter(
                    TournamentNew.status == StatusTournament.LIVE,
                    TournamentNew.is_active == True,
                )
                .outerjoin(
                    AthleteTournamentRegistration,
                    TournamentNew.id == AthleteTournamentRegistration.tournament_id,
                )
                .options(
                    joinedload(TournamentNew.registrations).joinedload(
                        AthleteTournamentRegistration.athlete
                    )
                )
                .all()
            )

            result = []
            for tournament in tournaments:
                athletes_count = (
                    session.query(count(distinct(AthleteRegistration.athlete_id)))
                    .join(
                        TournamentCategory,
                        TournamentCategory.tournament_category_id
                        == AthleteRegistration.tournament_category_id,
                    )
                    .filter(TournamentCategory.tournament_id == tournament.id)
                    .scalar()
                    or 0
                )

                live_fights_count = (
                    session.query(count(FightNew.id))
                    .join(
                        TournamentCategory,
                        TournamentCategory.tournament_category_id
                        == FightNew.tournament_category_id,
                    )
                    .filter(
                        TournamentCategory.tournament_id == tournament.id,
                        FightNew.status == FightStatus.LIVE,
                    )
                    .scalar()
                    or 0
                )

                result.append(
                    ActiveTournamentDTO.from_tournament(
                        tournament,
                        athletes_count=athletes_count,
                        live_fights_count=live_fights_count,
                    ).model_dump()
                )

        return {"success": True, "data": result, "total": len(result)}

    except Exception as e:
        return error_response(f"Ошибка при получении списка турниров: {str(e)}", 500)
