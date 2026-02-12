from flask import Blueprint, request, jsonify

from repository.athlete_repo import AthleteRepository
from repository.result_repo import ResultRepository

results_bp = Blueprint('results', __name__, url_prefix='/api/results')
result_repo = ResultRepository()

@results_bp.route('/', methods=['GET'])
def get_results():
    """Получить список результатов"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        category_id = request.args.get('category_id', type=int)

        if not tournament_id or not category_id:
            return jsonify({
                'success': False,
                'message': 'Обязательные параметры: tournament_id, category_id'
            }), 400

        results = result_repo.get_results_by_tournament(tournament_id, category_id)

        athlete_repo = AthleteRepository()
        result_data = []
        for result in results:
            result_data.append({
                'id': result.id,
                'fight_id': result.fight_id,
                'winner_name': athlete_repo.get_athlete_name_data(result.winner_id),
                'victory_type': result.victory_type.value,
                'fight_duration': result.fight_duration,
            })

        return jsonify({
            'success': True,
            'results': result_data,
            'total': len(result_data)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении результатов: {str(e)}'
        }), 500


# ХЗ как это сделать пока
# @results_bp.route('/tournament/<int:tournament_id>', methods=['GET'])
# def get_tournament_results(tournament_id):
#     """Получить результаты турнира"""
#     try:
#         calculator = ResultCalculator(tournament_id)
#
#         # Результаты по категориям
#         categories_results = []
#         for category in Category.query.filter_by(tournament_id=tournament_id).all():
#             results = calculator.calculate_category_results(category.id)
#             if results:
#                 categories_results.append({
#                     'category': category.name,
#                     'results': results
#                 })
#
#         # Командный зачет
#         team_ranking = calculator.calculate_team_ranking()
#
#         return jsonify({
#             'success': True,
#             'categories_results': categories_results,
#             'team_ranking': team_ranking
#         }), 200
#
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'message': f'Ошибка при получении результатов турнира: {str(e)}'
#         }), 500


@results_bp.route('/<int:result_id>', methods=['GET'])
def get_result(result_id):
    """Получить конкретный результат"""
    try:
        result = result_repo.get_result_by_id(result_id)

        if not result:
            return jsonify({
                'success': False,
                'message': 'Результат не найден'
            }), 404
        athlete_repo = AthleteRepository()
        return jsonify({
            'id': result.id,
            'fight_id': result.fight_id,
            'winner_name': athlete_repo.get_athlete_name_data(result.winner_id),
            'victory_type': result.victory_type.value,
            'fight_duration': result.fight_duration,
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении результата: {str(e)}'
        }), 500