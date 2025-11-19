from flask_restx import Namespace, Resource, fields
from flask import request
from models.result import Result
from models.fight import Fight
from services.result_calculator import ResultCalculator

results_ns = Namespace('results', description='Операции с результатами')

result_model = results_ns.model('Result', {
    'fight_id': fields.Integer(required=True),
    'winner_id': fields.Integer(required=True),
    'victory_type': fields.String(required=True),
    'details': fields.String()
})


@results_ns.route('/')
class ResultList(Resource):
    @results_ns.doc('list_results')
    def get(self):
        """Получить список результатов"""
        try:
            tournament_id = request.args.get('tournament_id', type=int)

            query = Result.query

            if tournament_id:
                query = query.join(Fight).filter(Fight.tournament_id == tournament_id)

            results = query.all()

            result_data = []
            for result in results:
                result_data.append({
                    'id': result.id,
                    'fight_id': result.fight_id,
                    'winner_name': result.winner.full_name if result.winner else None,
                    'victory_type': result.victory_type,
                    'victory_description': result.victory_description,
                    'fight_duration': result.fight_duration,
                    'technique_used': result.technique_used
                })

            return {
                'success': True,
                'results': result_data,
                'total': len(result_data)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении результатов: {str(e)}'
            }, 500


@results_ns.route('/tournament/<int:tournament_id>')
@results_ns.param('tournament_id', 'ID турнира')
class TournamentResults(Resource):
    @results_ns.doc('get_tournament_results')
    def get(self, tournament_id):
        """Получить результаты турнира"""
        try:
            calculator = ResultCalculator(tournament_id)

            # Результаты по категориям
            categories_results = []
            for category in Category.query.filter_by(tournament_id=tournament_id).all():
                results = calculator.calculate_category_results(category.id)
                if results:
                    categories_results.append({
                        'category': category.name,
                        'results': results
                    })

            # Командный зачет
            team_ranking = calculator.calculate_team_ranking()

            return {
                'success': True,
                'categories_results': categories_results,
                'team_ranking': team_ranking
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении результатов турнира: {str(e)}'
            }, 500