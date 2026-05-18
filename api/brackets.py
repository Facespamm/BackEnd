from flask import Blueprint, jsonify, request

from database.db import create_session
from repository.athlete_repo import AthleteRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from repository.tournament_repo import TournamentRepository
from services.bracket_generator import BracketGenerator

brackets_bp = Blueprint("brackets", __name__, url_prefix="/api/brackets")


@brackets_bp.route("/<int:tournament_id>", methods=["POST"])
def create_bracket(tournament_id):
    """Создает олимпийскую сетку"""
    try:
        category_str = request.args.get("category_id")
        if not category_str:
            return jsonify({"success": False, "message": "Не выбрана категория"}), 400

        tatami_number = request.args.get("tatami_number")
        if not tatami_number:
            return jsonify({"success": False, "message": "Татами не указан"}), 400

        try:
            category_id = int(category_str)
        except ValueError:
            return jsonify(
                {"success": False, "message": "ID категории должен быть целым числом"}
            ), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return jsonify({"success": False, "message": "Турнир не найден"}), 404

            category = tournament_repo.get_category(tournament_id, category_id)
            if not category:
                return jsonify(
                    {"success": False, "message": "Категория не найдена в этом турнире"}
                ), 404

        bracket_generator = BracketGenerator(tournament_id)
        generate_fights = bracket_generator.generate_olympic(category_id, tatami_number)

        if not generate_fights:
            return jsonify(
                {
                    "success": False,
                    "message": "Не удалось создать бои (возможно, недостаточно спортсменов в категории)",
                }
            ), 400

        return jsonify({"success": True, "message": "Сетка успешно создана"}), 201

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Ошибка создания сетки: {str(e)}"}
        ), 500


@brackets_bp.route("/<int:tournament_id>/has-consolation", methods=["GET"])
def has_consolation_fights(tournament_id):
    """Проверяет можно ли создать утешительные бои"""
    category_id = request.args.get("category_id", type=int)

    if not category_id:
        return jsonify({"success": False, "message": "ID категории не указан"}), 400

    with create_session() as session:
        tournament_repo = TournamentRepository(session)
        tournament_category = tournament_repo.get_tournament_category(
            tournament_id, category_id
        )

        if not tournament_category:
            return jsonify(
                {"success": False, "message": "Категория турнира не найдена"}
            ), 404

        if not tournament_category.has_consolidation_fights:
            return jsonify({"success": False}), 200

        athlete_repo = AthleteRepository(session)
        athletes = athlete_repo.get_athletes_by_tournament(tournament_id, category_id)

        total_rounds = BracketGenerator.calculate_rounds(len(athletes))

        fight_repo = FightRepository(session)
        semi_final_fights = fight_repo.get_semi_final_fights(
            tournament_category.tournament_category_id, total_rounds - 1
        )

    semi_final_fights_not_none = [
        f
        for f in semi_final_fights
        if f.blue_athlete_id is not None and f.white_athlete_id is not None
    ]

    if len(semi_final_fights_not_none) < 2:
        return jsonify({"success": False}), 200

    return jsonify({"success": True}), 200


@brackets_bp.route("/<int:tournament_id>/semifinals-consolation", methods=["POST"])
def generate_semifinals_consolation_fights(tournament_id):
    """Создание утешительных боев от полуфиналистов"""
    try:
        category_id = request.args.get("category", type=int)
        tatami_number = request.args.get("tatami_number", type=int)

        if not category_id or not tatami_number:
            return jsonify(
                {"success": False, "message": "Не выбрана категория или татами"}
            ), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return jsonify(
                    {"success": False, "message": "Категория турнира не найдена"}
                ), 404

        bracket_generator = BracketGenerator(tournament_id)
        generated_fights = (
            bracket_generator.generate_olympic_consolation_fight_semifinal(
                category_id, tatami_number
            )
        )

        if not generated_fights:
            return jsonify(
                {"success": False, "message": "Утешительные бои не созданы"}
            ), 400

        return jsonify(
            {"success": True, "message": "Утешительные бои успешно созданы"}
        ), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500


@brackets_bp.route("/<int:tournament_id>/finals-consolation", methods=["POST"])
def generate_consolation_fights_finalist(tournament_id):
    """Создание сетки для утешительных от финалистов"""
    try:
        category_id = request.args.get("category", type=int)
        if not category_id:
            return jsonify({"success": False, "message": "Не выбрана категория"}), 400

        tatami_number = request.args.get("tatami_number", type=int)
        if not tatami_number:
            return jsonify({"success": False, "message": "Не выбран татами"}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return jsonify(
                    {"success": False, "message": "Категория турнира не найдена"}
                ), 404

        bracket_generator = BracketGenerator(tournament_id)
        generated_fights = bracket_generator.generate_olympic_consolation_fight_final(
            category_id, tatami_number
        )

        if not generated_fights:
            return jsonify(
                {"success": False, "message": "Утешительные бои не созданы"}
            ), 404

        return jsonify(
            {"success": True, "message": "Утешительные бои успешно созданы"}
        ), 201

    except Exception as e:
        return jsonify(
            {
                "success": False,
                "message": f"Ошибка создания утешительных боев: {str(e)}",
            }
        ), 500


@brackets_bp.route("/<int:tournament_id>/fights", methods=["GET"])
def fight_bracket(tournament_id):
    try:
        category_id = request.args.get("category")
        if not category_id:
            return jsonify({"success": False, "message": "Не выбрана категория"}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return jsonify(
                    {"success": False, "message": "Категория турнира не найдена"}
                ), 404

            tournament_category_id = tournament_category.tournament_category_id

            fight_repo = FightRepository(session)
            fights = fight_repo.get_fight_by_tournament(tournament_category_id)

            athlete_repo = AthleteRepository(session)
            fights_dtos = [
                {
                    "id": fight.id,
                    "blue_athlete": athlete_repo.get_athlete_by_fight(
                        fight.blue_athlete_id, fight.id
                    ),
                    "white_athlete": athlete_repo.get_athlete_by_fight(
                        fight.white_athlete_id, fight.id
                    ),
                    "tatami_number": fight.tatami_number,
                    "round": fight.round_number,
                    "status_fight": fight.status.value,
                    "next_fight": fight.next_fight_id,
                    "type_bracket": fight.type_bracket.value,
                }
                for fight in fights
            ]

            tournament_name = (
                tournament_repo.get_tournament_name_by_tournament_category(
                    tournament_category_id
                )
            )

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(category_id)
            # ✅ Извлекаем все данные из объекта ВНУТРИ сессии
            category_dto = (
                {
                    "id": category.id,
                    "name": category.name,
                    "weight_range": f"от {category.min_weight} до {category.max_weight}",
                }
                if category
                else None
            )

            winner = None
            if fights:
                last_fight = fights[-1]
                result_repo = ResultRepository(session)
                has_result = result_repo.get_result_by_fight(last_fight.id)
                if has_result:
                    winner = athlete_repo.get_athlete_by_fight(
                        has_result.winner_id, last_fight.id
                    )

        if not fights_dtos:
            return jsonify({"success": False, "message": "Нет боев"}), 404

        return jsonify(
            {
                "success": True,
                "fights": fights_dtos,
                "tournament_name": tournament_name,
                "category": category_dto,
                "winner": winner,
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Ошибка вывода боев: {str(e)}"}
        ), 500


@brackets_bp.route("/<int:tournament_id>/first_fights", methods=["GET"])
def first_fights(tournament_id):
    try:
        category_id = request.args.get("category")
        if not category_id:
            return jsonify({"success": False, "message": "Не выбрана категория"}), 400

        with create_session() as session:
            tournament_repo = TournamentRepository(session)
            tournament_category = tournament_repo.get_tournament_category(
                tournament_id, category_id
            )
            if not tournament_category:
                return jsonify(
                    {"success": False, "message": "Категория турнира не найдена"}
                ), 404

            tournament_category_id = tournament_category.tournament_category_id

            fight_repo = FightRepository(session)
            fights = fight_repo.get_fight_by_tournament(
                tournament_category_id, minimal_round_number=1
            )  # самый первый раунд это первый

            athlete_repo = AthleteRepository(session)
            fights_dtos = [
                {
                    "id": fight.id,
                    "blue_athlete": athlete_repo.get_athlete_by_fight(
                        fight.blue_athlete_id, fight.id
                    ),
                    "white_athlete": athlete_repo.get_athlete_by_fight(
                        fight.white_athlete_id, fight.id
                    ),
                    "tatami_number": fight.tatami_number,
                    "round": fight.round_number,
                    "status_fight": fight.status.value,
                    "next_fight": fight.next_fight_id,
                    "type_bracket": fight.type_bracket.value,
                }
                for fight in fights
            ]

            tournament_name = (
                tournament_repo.get_tournament_name_by_tournament_category(
                    tournament_category_id
                )
            )

            category_repo = CategoryRepository(session)
            category = category_repo.get_category_by_id(category_id)
            # ✅ Извлекаем все данные из объекта ВНУТРИ сессии
            category_dto = (
                {
                    "id": category.id,
                    "name": category.name,
                    "weight_range": f"от {category.min_weight} до {category.max_weight}",
                }
                if category
                else None
            )

            winner = None
            if fights:
                last_fight = fights[-1]
                result_repo = ResultRepository(session)
                has_result = result_repo.get_result_by_fight(last_fight.id)
                if has_result:
                    winner = athlete_repo.get_athlete_by_fight(
                        has_result.winner_id, last_fight.id
                    )

        if not fights_dtos:
            return jsonify({"success": False, "message": "Нет боев"}), 404

        return jsonify(
            {
                "success": True,
                "fights": fights_dtos,
                "tournament_name": tournament_name,
                "category": category_dto,
                "winner": winner,
            }
        )
    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Ошибка вывода боев: {str(e)}"}
        ), 500
