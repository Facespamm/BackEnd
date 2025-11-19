from flask_restx import Namespace, Resource, fields
from flask import request
from models.athlete import Athlete
from models.club import Club
from database.db import db

athletes_ns = Namespace('athletes', description='Операции с участниками')

athlete_model = athletes_ns.model('Athlete', {
    'first_name': fields.String(required=True),
    'last_name': fields.String(required=True),
    'middle_name': fields.String(),
    'birth_date': fields.String(required=True),
    'gender': fields.String(required=True),
    'club_id': fields.Integer(),
    'rank': fields.String(),
    'license_number': fields.String(),
    'phone': fields.String(),
    'email': fields.String(),
    'medical_check': fields.Boolean()
})


@athletes_ns.route('/')
class AthleteList(Resource):
    @athletes_ns.doc('list_athletes')
    def get(self):
        """Получить список участников"""
        try:
            club_id = request.args.get('club_id', type=int)
            search = request.args.get('search', '')

            query = Athlete.query.filter_by(is_active=True)

            if club_id:
                query = query.filter_by(club_id=club_id)

            if search:
                query = query.filter(
                    db.or_(
                        Athlete.last_name.ilike(f'%{search}%'),
                        Athlete.first_name.ilike(f'%{search}%')
                    )
                )

            athletes = query.order_by(Athlete.last_name, Athlete.first_name).all()

            result = []
            for athlete in athletes:
                result.append({
                    'id': athlete.id,
                    'first_name': athlete.first_name,
                    'last_name': athlete.last_name,
                    'middle_name': athlete.middle_name,
                    'full_name': athlete.full_name,
                    'birth_date': athlete.birth_date.isoformat(),
                    'age': athlete.age,
                    'gender': athlete.gender,
                    'club': athlete.club.name if athlete.club else None,
                    'rank': athlete.rank,
                    'license_number': athlete.license_number
                })

            return {
                'success': True,
                'athletes': result,
                'total': len(result)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении участников: {str(e)}'
            }, 500

    @athletes_ns.expect(athlete_model)
    @athletes_ns.doc('create_athlete')
    def post(self):
        """Создать нового участника"""
        try:
            data = request.json

            # Валидация
            if not data.get('first_name') or not data.get('last_name') or not data.get('birth_date'):
                return {
                    'success': False,
                    'message': 'Обязательные поля: first_name, last_name, birth_date'
                }, 400

            athlete = Athlete(
                first_name=data['first_name'],
                last_name=data['last_name'],
                middle_name=data.get('middle_name'),
                birth_date=datetime.fromisoformat(data['birth_date']),
                gender=data['gender'],
                club_id=data.get('club_id'),
                rank=data.get('rank'),
                license_number=data.get('license_number'),
                phone=data.get('phone'),
                email=data.get('email'),
                medical_check=data.get('medical_check', False)
            )

            if athlete.save():
                return {
                    'success': True,
                    'message': 'Участник успешно создан',
                    'athlete_id': athlete.id
                }, 201
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при сохранении участника'
                }, 400

        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при создании участника: {str(e)}'
            }, 500


@athletes_ns.route('/<int:athlete_id>')
@athletes_ns.param('athlete_id', 'ID участника')
class AthleteDetail(Resource):
    @athletes_ns.doc('get_athlete')
    def get(self, athlete_id):
        """Получить информацию об участнике"""
        try:
            athlete = Athlete.query.get(athlete_id)
            if not athlete:
                return {
                    'success': False,
                    'message': 'Участник не найден'
                }, 404

            return {
                'success': True,
                'athlete': {
                    'id': athlete.id,
                    'first_name': athlete.first_name,
                    'last_name': athlete.last_name,
                    'middle_name': athlete.middle_name,
                    'full_name': athlete.full_name,
                    'birth_date': athlete.birth_date.isoformat(),
                    'age': athlete.age,
                    'gender': athlete.gender,
                    'club_id': athlete.club_id,
                    'club_name': athlete.club.name if athlete.club else None,
                    'rank': athlete.rank,
                    'license_number': athlete.license_number,
                    'phone': athlete.phone,
                    'email': athlete.email,
                    'medical_check': athlete.medical_check
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка при получении участника: {str(e)}'
            }, 500