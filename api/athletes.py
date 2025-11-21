from flask import request, Blueprint, jsonify
from flasgger import swag_from
from databse.db import db
from models.athlete import Athlete
import datetime

athletes_bp = Blueprint('athletes', __name__, url_prefix='/athletes')


@athletes_bp.route('/', methods=['GET'])
@swag_from({
    "summary": "Получить список участников",
    "tags": ["Участники"],
    "parameters": [
        {
            "name": "club_id",
            "in": "query",
            "type": "integer",
            "required": False,
            "description": "Фильтр по ID клуба"
        },
        {
            "name": "search",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Поиск по фамилии или имени"
        }
    ],
    "responses": {
        "200": {
            "description": "Список участников",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "athletes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "first_name": {"type": "string"},
                                        "last_name": {"type": "string"},
                                        "middle_name": {"type": "string", "nullable": True},
                                        "full_name": {"type": "string"},
                                        "birth_date": {"type": "string", "format": "date"},
                                        "age": {"type": "integer"},
                                        "gender": {"type": "string", "enum": ["М", "Ж"]},
                                        "club": {"type": "string", "nullable": True},
                                        "rank": {"type": "string", "nullable": True},
                                        "license_number": {"type": "string", "nullable": True}
                                    }
                                }
                            },
                            "total": {"type": "integer"}
                        }
                    },
                    "example": {
                        "success": True,
                        "total": 2,
                        "athletes": [
                            {
                                "id": 1,
                                "first_name": "Иван",
                                "last_name": "Иванов",
                                "middle_name": "Иванович",
                                "full_name": "Иванов Иван Иванович",
                                "birth_date": "2010-05-15",
                                "age": 15,
                                "gender": "М",
                                "club": "СК Луч",
                                "rank": "1 юн",
                                "license_number": "123456"
                            }
                        ]
                    }
                }
            }
        }
    }
})
def get_athletes():
    """Получить список участников"""
    try:
        club_id = request.args.get('club_id', type=int)
        search = request.args.get('search', '').strip()

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

        return jsonify({
            'success': True,
            'athletes': result,
            'total': len(result)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участников: {str(e)}'
        }), 500


@athletes_bp.route('/', methods=['POST'])
@swag_from({
    "summary": "Создать нового участника",
    "tags": ["Участники"],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["first_name", "last_name", "birth_date", "gender"],
                    "properties": {
                        "first_name": {"type": "string", "example": "Алексей"},
                        "last_name": {"type": "string", "example": "Петров"},
                        "middle_name": {"type": "string", "example": "Сергеевич", "nullable": True},
                        "birth_date": {"type": "string", "format": "date", "example": "2008-03-22"},
                        "gender": {"type": "string", "enum": ["М", "Ж"], "example": "М"},
                        "club_id": {"type": "integer", "example": 5, "nullable": True},
                        "rank": {"type": "string", "example": "1 разряд", "nullable": True},
                        "license_number": {"type": "string", "example": "ABC123456", "nullable": True},
                        "phone": {"type": "string", "example": "+79991234567", "nullable": True},
                        "email": {"type": "string", "example": "petrov@example.com", "nullable": True},
                        "medical_check": {"type": "boolean", "example": True}
                    }
                }
            }
        }
    },
    "responses": {
        "201": {
            "description": "Участник успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Участник успешно создан",
                        "athlete_id": 42
                    }
                }
            }
        },
        "400": {
            "description": "Ошибка валидации или сохранения"
        }
    }
})
def create_athlete():
    """Создать нового участника"""
    try:
        data = request.get_json() or {}

        required = ['first_name', 'last_name', 'birth_date', 'gender']
        missing = [field for field in required if not data.get(field)]
        if missing:
            return jsonify({
                'success': False,
                'message': f'Обязательные поля: {", ".join(missing)}'
            }), 400

        athlete = Athlete(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            middle_name=data.get('middle_name', '').strip() or None,
            birth_date=datetime.datetime.fromisoformat(data['birth_date']),
            gender=data['gender'],
            club_id=data.get('club_id'),
            rank=data.get('rank'),
            license_number=data.get('license_number'),
            phone=data.get('phone'),
            email=data.get('email'),
            medical_check=data.get('medical_check', False)
        )

        if athlete.save():
            return jsonify({
                'success': True,
                'message': 'Участник успешно создан',
                'athlete_id': athlete.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении участника'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании участника: {str(e)}'
        }), 500


@athletes_bp.route('/<int:athlete_id>', methods=['GET'])
@swag_from({
    "summary": "Получить участника по ID",
    "tags": ["Участники"],
    "parameters": [
        {
            "name": "athlete_id",
            "in": "path",
            "required": True,
            "type": "integer",
            "description": "ID участника"
        }
    ],
    "responses": {
        "200": {
            "description": "Информация об участнике",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                            "athlete": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "first_name": {"type": "string"},
                                    "last_name": {"type": "string"},
                                    "middle_name": {"type": "string", "nullable": True},
                                    "full_name": {"type": "string"},
                                    "birth_date": {"type": "string", "format": "date"},
                                    "age": {"type": "integer"},
                                    "gender": {"type": "string"},
                                    "club_id": {"type": "integer", "nullable": True},
                                    "club_name": {"type": "string", "nullable": True},
                                    "rank": {"type": "string", "nullable": True},
                                    "license_number": {"type": "string", "nullable": True},
                                    "phone": {"type": "string", "nullable": True},
                                    "email": {"type": "string", "nullable": True},
                                    "medical_check": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "404": {
            "description": "Участник не найден"
        }
    }
})
def get_athlete_by_id(athlete_id):
    """Получить информацию об участнике"""
    try:
        athlete = Athlete.query.get(athlete_id)
        if not athlete or not athlete.is_active:
            return jsonify({
                'success': False,
                'message': 'Участник не найден'
            }), 404

        return jsonify({
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
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участника: {str(e)}'
        }), 500