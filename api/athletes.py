from flask import request, Blueprint, jsonify
from flasgger import swag_from
from flask_jwt_extended import get_jwt_identity, jwt_required
from database.db import db
from new_model.Enums import translate_gender, RoleName
import datetime

from new_model.head_model.new_athlete import AthleteNew
from repository.athlete_repo import AthleteRepository
from repository.auth_repo import AuthRepository
from repository.category_repo import CategoryRepository

athletes_bp = Blueprint('athletes', __name__, url_prefix='/athletes')
athlete_repo = AthleteRepository()

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
            "description": "Список участников"
        }
    }
})
def get_athletes():
    """Получить список участников"""
    try:
        club_id = request.args.get('club_id', type=int)
        search = request.args.get('search', '').strip()

        athletes = athlete_repo.get_athletes(club_id, search)

        result = []
        for athlete in athletes:
            result.append({
                'id': athlete.id,
                'first_name': athlete.user.first_name,
                'last_name': athlete.user.last_name,
                'middle_name': athlete.user.middle_name,
                'full_name': athlete.full_name,
                'birth_date': athlete.birth_date.isoformat(),
                'age': athlete.age,
                'gender': athlete.gender,
                'club': athlete.club.name if athlete.club else None,
                'club_id': athlete.club_id,
                 'rank': athlete.rank.level if athlete.rank else None,
                'rank_id': athlete.rank_id,
                'license_number': athlete.license_number,
                'phone': athlete.user.phone,
                'email': athlete.user.email
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

@athletes_bp.route('/<int:user_id>', methods=['POST'])
@swag_from({
    "summary": "Создать нового участника",
    "tags": ["Участники"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["birth_date", "gender", "club_id", "rank_id", "license_number", "medical_check",
                             "insurance_number"],
                "properties": {
                    "birth_date": {"type": "string", "format": "date", "example": "2008-03-22"},
                    "gender": {"type": "string", "enum": ["М", "Ж"], "example": "М"},
                    "club_id": {"type": "integer", "example": 5},
                    "rank_id": {"type": "integer", "example": 3},
                    "license_number": {"type": "string", "example": "ABC123456"},
                    "medical_check": {"type": "boolean", "example": True},
                    "insurance_number": {"type": "string", "example": "INS123456"}
                }
            }
        }
    ],
    "responses": {
        "201": {
            "description": "Участник успешно создан"
        },
        "400": {
            "description": "Ошибка валидации или сохранения"
        }
    }
})
def create_athlete(user_id):
    """Создать нового участника"""
    try:
        data = request.get_json() or {}

        if not user_id:
            return jsonify({'success': False,'message': f"Нет user id"})

        # Нормализуем названия полей
        if 'birth_day' in data and 'birth_date' not in data:
            data['birth_date'] = data['birth_day']

        if 'gender' in data:
            data['gender'] = translate_gender(data['gender'])

        # Проверяем обязательные поля (только для атлета, без данных пользователя)
        required = ['birth_date', 'gender', 'club_id', 'rank_id', 'license_number', 'medical_check', 'insurance_number','age','weight']
        missing = [field for field in required if field not in data]
        if missing:
            return jsonify({
                'success': False,
                'message': f'Обязательные поля: {", ".join(missing)}'
            }), 400

        # Создаем профиль участника
        athlete = AthleteNew(
            user_id=user_id,
            birth_date=datetime.datetime.fromisoformat(data['birth_date']).date(),
            gender=data['gender'],
            club_id=data['club_id'],
            rank_id=data['rank_id'],
            license_number=data['license_number'],
            medical_check=data['medical_check'],
            insurance_number=data['insurance_number'],
            is_active=True
        )

        auth_repo = AuthRepository()
        role_id = auth_repo.get_role_id(RoleName.ATHLETE.value)
        auth_repo.update_user_role(user_id, role_id)

        athlete_is_added = athlete_repo.create_athlete(athlete)

        if not athlete_is_added:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении участника'
            }), 400

        category_repo = CategoryRepository()
        category_added = category_repo.add_athlete_to_category(athlete)

        if category_added:
            return jsonify({
                'success': True,
                'message': 'Участник успешно создан, добавлен в категорию',
                'athlete_id': athlete.id,
                'user_id': user_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении участника в категорию'
            }), 400


    except Exception as e:
        db.session.rollback()
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
            "description": "Информация об участнике"
        },
        "404": {
            "description": "Участник не найден"
        }
    }
})
def get_athlete_by_id(athlete_id):
    """Получить информацию об участнике"""
    try:
        athlete = athlete_repo.get_athlete_by_id(athlete_id)
        if not athlete or not athlete.is_active:
            return jsonify({
                'success': False,
                'message': 'Участник не найден'
            }), 404

        return jsonify({
            'success': True,
            'athlete': {
                'id': athlete.id,
                'first_name': athlete.user.first_name,
                'last_name': athlete.user.last_name,
                'middle_name': athlete.user.middle_name,
                'full_name': athlete.full_name,
                'birth_date': athlete.birth_date.isoformat(),
                'age': athlete.age,
                'gender': athlete.gender,
                'club_id': athlete.club_id,
                'club_name': athlete.club.name if athlete.club else None,
                'rank': athlete.rank.level if athlete.rank else None,
                'rank_id': athlete.rank_id,
                'license_number': athlete.license_number,
                'phone': athlete.user.phone,
                'email': athlete.user.email,
                'medical_check': athlete.medical_check,
                'insurance_number': athlete.insurance_number
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участника: {str(e)}'
        }), 500

@athletes_bp.route('/<int:athlete_id>', methods=['PUT'])
@swag_from({
    "summary": "Обновить информацию об участнике",
    "tags": ["Участники"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "parameters": [
        {
            "name": "athlete_id",
            "in": "path",
            "required": True,
            "type": "integer",
            "description": "ID участника"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "middle_name": {"type": "string"},
                    "birth_date": {"type": "string", "format": "date"},
                    "gender": {"type": "string", "enum": ["М", "Ж"]},
                    "club_id": {"type": "integer"},
                    "rank_id": {"type": "integer"},
                    "license_number": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "medical_check": {"type": "boolean"},
                    "insurance_number": {"type": "string"}
                }
            }
        }
    ],
    "responses": {
        "200": {
            "description": "Участник успешно обновлен"
        },
        "404": {
            "description": "Участник не найден"
        },
        "400": {
            "description": "Ошибка при обновлении"
        }
    }
})
def update_athlete(athlete_id):
    """Обновить информацию об участнике"""
    try:
        athlete = athlete_repo.get_athlete_by_id(athlete_id)
        if not athlete or not athlete.is_active:
            return jsonify({
                'success': False,
                'message': 'Участник не найден'
            }), 404

        data = request.get_json() or {}

        # Обновляем данные пользователя
        user_fields = ['first_name', 'last_name', 'middle_name', 'phone', 'email']
        # Обновляем данные участника
        athlete_fields = ['birth_date', 'gender', 'club_id', 'rank_id',
                          'license_number', 'medical_check', 'insurance_number']

        is_updated = athlete_repo.update_athlete(athlete, data, user_fields, athlete_fields,data)

        if is_updated:
            return jsonify({
                'success': True,
                'message': 'Участник успешно обновлен',
                'athlete_id': athlete.id
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Ошибка при сохранении'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении участника: {str(e)}'
        }), 500

@athletes_bp.route('/<int:athlete_id>', methods=['DELETE'])
@swag_from({
    "summary": "Удалить участника",
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
            "description": "Участник успешно удален"
        },
        "404": {
            "description": "Участник не найден"
        },
        "400": {
            "description": "Ошибка при удалении"
        }
    }
})
def delete_athlete(athlete_id):
    """Удалить участника (мягкое удаление)"""
    try:
        athlete = athlete_repo.get_athlete_by_id(athlete_id)
        if not athlete or not athlete.is_active:
            return jsonify({
                'success': False,
                'message': 'Участник не найден'
            }), 404

        # Мягкое удаление - помечаем как неактивного
        is_deleted = athlete_repo.delete_athlete_by_id(athlete_id)

        if is_deleted:
            return jsonify({
                'success': True,
                'message': 'Участник удален'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': f'Ошибка при удалении'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении участника: {str(e)}'
        }), 500