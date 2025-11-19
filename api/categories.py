from flask_restx import Namespace, Resource, fields
from flask import request
from models.category import Category
from models.tournament import Tournament

categories_ns = Namespace('categories', description='Операции с категориями')

category_model = categories_ns.model('Category', {
    'tournament_id': fields.Integer(required=True),
    'name': fields.String(required=True),
    'gender': fields.String(required=True),
    'min_weight': fields.Float(),
    'max_weight': fields.Float(),
    'min_age': fields.Integer(),
    'max_age': fields.Integer()
})


@categories_ns.route('/')
class CategoryList(Resource):
    @categories_ns.doc('list_categories')
    def get(self):
        """Получить список категорий"""
        try:
            tournament_id = request.args.get('tournament_id', type=int)

            query = Category.query

            if tournament_id:
                query = query.filter_by(tournament_id=tournament_id)

            categories = query.filter_by(is_active=True).all()

            result = []
            for category in categories:
                result.append({
                    'id': category.id,
                    'name': category.name,
                    'gender': category.gender,
                    'weight_range': category.weight_range,
                    'age_range': category.age_range,
                    'athletes_count': category.athletes_count,
                    'tournament_id': category.tournament_id
                })

            return {
                'success': True,
                'categories': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении категорий: {str(e)}'
            }, 500

    @categories_ns.expect(category_model)
    @categories_ns.doc('create_category')
    def post(self):
        """Создать новую категорию"""
        try:
            data = request.json

            if not data.get('name') or not data.get('tournament_id') or not data.get('gender'):
                return {
                    'success': False,
                    'message': 'Обязательные поля: name, tournament_id, gender'
                }, 400

            # Проверяем существование турнира
            tournament = Tournament.query.get(data['tournament_id'])
            if not tournament:
                return {
                    'success': False,
                    'message': 'Турнир не найден'
                }, 404

            category = Category(
                tournament_id=data['tournament_id'],
                name=data['name'],
                gender=data['gender'],
                min_weight=data.get('min_weight'),
                max_weight=data.get('max_weight'),
                min_age=data.get('min_age'),
                max_age=data.get('max_age')
            )

            if category.save():
                return {
                    'success': True,
                    'message': 'Категория успешно создана',
                    'category_id': category.id
                }, 201
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при сохранении категории'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при создании категории: {str(e)}'
            }, 500


@categories_ns.route('/<int:category_id>/athletes')
@categories_ns.param('category_id', 'ID категории')
class CategoryAthletes(Resource):
    @categories_ns.doc('get_category_athletes')
    def get(self, category_id):
        """Получить участников категории"""
        try:
            category = Category.query.get(category_id)
            if not category:
                return {
                    'success': False,
                    'message': 'Категория не найдена'
                }, 404

            athletes = []
            for athlete in category.athletes:
                athletes.append({
                    'id': athlete.id,
                    'full_name': athlete.full_name,
                    'club': athlete.club.name if athlete.club else None,
                    'age': athlete.age,
                    'rank': athlete.rank
                })

            return {
                'success': True,
                'category': category.name,
                'athletes': athletes,
                'total': len(athletes)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении участников категории: {str(e)}'
            }, 500