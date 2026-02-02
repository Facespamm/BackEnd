from flask import Blueprint, jsonify, request

from new_model.Enums import text_to_referee_level
from new_model.handbook.new_referee import RefereeNew
from repository.figth_repo import FightRepository
from repository.referee_repo import RefereeRepository
from repository.tournament_repo import TournamentRepository

referee_bp = Blueprint("referee", __name__, url_prefix="/referee")
referee_repo = RefereeRepository()

@referee_bp.route("/", methods=["GET"])
def get_referees():
    try:
        referees = referee_repo.get_referees()

        results = []
        for referee in referees:
            referee_dto = {
                'id': referee.id,
                'first_name': referee.first_name,
                'last_name': referee.last_name,
                'middle_name': referee.middle_name,
                'email': referee.email,
                'phone': referee.phone,
                'certification_level': referee.certification_level.value,
            }

            results.append(referee_dto)


        return jsonify({
            'referees': results,
            'count_referees': len(results)
        }),200

    except Exception as e:
        print(f"Error in get_referees: {e}")
        return jsonify({
            'message': 'Проблеммы с получением судей',
        }), 500

@referee_bp.route("/<referee_id>", methods=["GET"])
def get_referee(referee_id):
    try:
        if not referee_id:
            return jsonify({
                'message':'Не выбран судья'
            }), 400

        referee = referee_repo.get_referee(referee_id)

        referee_dto = {
            'id': referee.id,
            'first_name': referee.first_name,
            'last_name': referee.last_name,
            'middle_name': referee.middle_name,
            'email': referee.email,
            'phone': referee.phone,
            'certification_level': referee.certification_level.value,
        }

        return jsonify({
            'referee': referee_dto
        }), 200
    except Exception as e:
        print(f"Error in get_referee: {e}")
        return jsonify({
            'message':'Ошибка получение судьи'
        }), 500

@referee_bp.route("/", methods=["POST"])
def create_referee():
    try:
        data = request.get_json()

        required_fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone', 'certification_level']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                'message': f'Не заполненно следующие поля {missing_fields}'
            }), 400

        new_referee = RefereeNew(
            first_name=data['first_name'],
            last_name=data['last_name'],
            middle_name=data['middle_name'],
            email=data['email'],
            phone=data['phone'],
            certification_level=text_to_referee_level(data['certification_level']),
        )

        is_added = referee_repo.create_referee(new_referee)

        if is_added:
            return jsonify({
                'message': 'Судья создан',
                'referee_id': new_referee.id
            }), 200
        else:
            return jsonify({
                'message':'Судья не создан'
            }), 500

    except Exception as e:
        print(f"Error in create_referee: {e}")
        return jsonify({
            'message': 'Прогблемма создание судьи'
        }), 500

@referee_bp.route("/<referee_id>", methods=["PUT"])
def update_referee(referee_id):
    try:
        data = request.get_json()

        if not referee_id:
            return jsonify({
                'message': 'Не выбрано судья'
            }), 400

        required_fields = ['email', 'phone', 'certification_level']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                'message': f"Заполните вот эти поля {missing_fields}"
            }), 400

        data['certification_level'] = text_to_referee_level(data['certification_level'])
        referee = referee_repo.get_referee(referee_id)
        if not referee:
            return jsonify({
                'message': 'Не найден такой судья'
            }), 404

        is_updated = referee_repo.update_referee(referee, data)

        if is_updated:
            return jsonify({
                'message': 'Данные обнавленны'
            }), 200
        else:
            return jsonify({
                'message': 'Не получилось обновить'
            }),400
    except Exception as e:
        print(f"Error in update_referee: {e}")
        return jsonify({
            'message': 'Ошибка обнавления'
        }),500

@referee_bp.route("/<tournament_id>/assign_to-fights", methods=["POST"])
def assign_referees_to_fights(tournament_id):
    try:
        if not tournament_id:
            return jsonify({
                'message': 'Не выбран турнир'
            }), 400

        category = request.args.get('category')
        if not category:
            return jsonify({
                'message': 'Не выбрана категория'
            }), 400

        data = request.get_json()

        required_fields = ['referees']

        if not all(field in data for field in required_fields):
            return jsonify({
                'message': f'Не заполненно следующие поля {required_fields}'
            }), 400

        if not data['referees'] or len(data['referees']) != 3:
            return jsonify({
                'message': 'Список судей пуст'
            }), 400

        tournament_repo = TournamentRepository()
        tournament_category = tournament_repo.get_tournament_category(tournament_id, category)

        if not tournament_category:
            return jsonify({
                'message': 'Нет такой категории в турнире'
            }), 404

        fight_repo = FightRepository()
        figths = fight_repo.get_fight_by_tournament(tournament_category.tournament_category_id)

        if not figths:
            return jsonify({
                'message': 'В этой категории нет боев'
            }), 404
        referees = data['referees']
        for fight in figths:
            fight_repo.assign_referee(referees[0], fight.id,"Главный")
            fight_repo.assign_referee(referees[1], fight.id,"Второй")
            fight_repo.assign_referee(referees[2], fight.id,"Третий")

        return jsonify({
            'message': 'Судьи назначены на бои'
        }), 200
    except Exception as e:
        print(f"Error in assign_referees_to_fights: {e}")
        return jsonify({
            'message': 'Ошибка назначения судей на бои'
        }), 500


@referee_bp.route("/<referee_id>", methods=["DELETE"])
def delete_referee(referee_id):
    try:
        if not referee_id:
            return jsonify({
                'message': 'Не выбран Судья для удаления'
            }), 400

        referee = referee_repo.get_referee(referee_id)
        if not referee:
            return jsonify({
                'message':'Нет такого судьи'
            }), 404

        is_deleted = referee_repo.delete_referee(referee.id)

        if is_deleted:
            return jsonify({
                'message': 'Судья удален'
            }), 200
        else:
            return jsonify({
                'message': 'Ошибка удаления судьи'
            }), 400
    except Exception as e:
        print(f"Error in delete_referee: {e}")
        return jsonify({
            'message': 'Ошибка удаления'
        }), 500