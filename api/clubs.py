from flask_restx import Namespace, Resource, fields
from flask import request
from models.club import Club

clubs_ns = Namespace('clubs', description='Операции с клубами')

club_model = clubs_ns.model('Club', {
    'name': fields.String(required=True),
    'short_name': fields.String(),
    'city': fields.String(),
    'country': fields.String(),
    'address': fields.String(),
    'phone': fields.String(),
    'email': fields.String(),
    'website': fields.String(),
    'coach_name': fields.String(),
    'founded_year': fields.Integer()
})


@clubs_ns.route('/')
class ClubList(Resource):
    @clubs_ns.doc('list_clubs')
    def get(self):
        """Получить список клубов"""
        try:
            clubs = Club.query.filter_by(is_active=True).order_by(Club.name).all()

            result = []
            for club in clubs:
                result.append({
                    'id': club.id,
                    'name': club.name,
                    'short_name': club.short_name,
                    'city': club.city,
                    'country': club.country,
                    'coach_name': club.coach_name,
                    'athletes_count': club.athletes_count
                })

            return {
                'success': True,
                'clubs': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении клубов: {str(e)}'
            }, 500

    @clubs_ns.expect(club_model)
    @clubs_ns.doc('create_club')
    def post(self):
        """Создать новый клуб"""
        try:
            data = request.json

            if not data.get('name'):
                return {
                    'success': False,
                    'message': 'Название клуба обязательно'
                }, 400

            club = Club(
                name=data['name'],
                short_name=data.get('short_name'),
                city=data.get('city'),
                country=data.get('country', 'Россия'),
                address=data.get('address'),
                phone=data.get('phone'),
                email=data.get('email'),
                website=data.get('website'),
                coach_name=data.get('coach_name'),
                founded_year=data.get('founded_year')
            )

            if club.save():
                return {
                    'success': True,
                    'message': 'Клуб успешно создан',
                    'club_id': club.id
                }, 201
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при сохранении клуба'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при создании клуба: {str(e)}'
            }, 500