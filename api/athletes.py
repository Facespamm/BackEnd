from flask import request, Blueprint, jsonify
from database.db import db
from new_model.Enums import translate_gender, RoleName
from datetime import datetime

from new_model.head_model.new_athlete import AthleteNew
from repository.athlete_repo import AthleteRepository
from repository.auth_repo import AuthRepository
from dateutil.relativedelta import relativedelta

athletes_bp = Blueprint('athletes', __name__, url_prefix='/api/athletes')
athlete_repo = AthleteRepository()

@athletes_bp.route('/', methods=['GET'])
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
def create_athlete(user_id):
    """Создать нового участника"""
    try:
        data = request.get_json() or {}

        if not user_id:
            return jsonify({'success': False,'message': f"Нет user id"})

        has_athlete = athlete_repo.has_athlete(user_id)

        if has_athlete:
            return jsonify({'success': False,'message': f"У этого пользователя уже есть профиль участника"}), 400

        # Нормализуем названия полей
        if 'birth_day' in data and 'birth_date' not in data:
            data['birth_date'] = data['birth_day']

        if 'gender' in data:
            data['gender'] = translate_gender(data['gender'])

        # Проверяем обязательные поля (только для атлета, без данных пользователя)
        required = ['birth_date', 'gender', 'club_id', 'rank_id', 'license_number', 'medical_check', 'insurance_number','weight']
        missing = [field for field in required if field not in data]
        if missing:
            return jsonify({
                'success': False,
                'message': f'Обязательные поля: {", ".join(missing)}'
            }), 400

        date_now = datetime.now()
        birth_date = datetime.fromisoformat(data['birth_date'])

        years = relativedelta(date_now, birth_date).years

        # Создаем профиль участника
        athlete = AthleteNew(
            user_id=user_id,
            birth_date=datetime.fromisoformat(data['birth_date']).date(),
            gender=data['gender'],
            club_id=data['club_id'],
            rank_id=data['rank_id'],
            license_number=data['license_number'],
            medical_check=data['medical_check'],
            insurance_number=data['insurance_number'],
            age = years,
            is_active=True
        )

        auth_repo = AuthRepository()
        role_id = auth_repo.get_role_id(RoleName.ATHLETE.value)
        auth_repo.update_user_role(user_id, role_id)

        athlete_repo.set_category(athlete,data['weight'])
        athlete_is_added = athlete_repo.create_athlete(athlete)

        if not athlete_is_added:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении участника в категорию'
            }), 400
        else:
            return jsonify({
                'success': True,
                'message': 'Участник успешно создан, добавлен в категорию',
                'athlete_id': athlete.id,
                'user_id': user_id
            }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании участника: {str(e)}'
        }), 500

@athletes_bp.route('/<int:athlete_id>', methods=['GET'])
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
        is_deleted = athlete_repo.delete_athlete(athlete)

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

@athletes_bp.route('/search-athlete', methods=['GET'])
def search_athlete():
    """Поиск участника по ФИО для получения его ID"""
    try:
        # Получаем параметры поиска
        last_name = request.args.get('last_name', '').strip()
        first_name = request.args.get('first_name', '').strip()
        middle_name = request.args.get('middle_name', '').strip()
        club_id = request.args.get('club_id')
        # is_active = request.args.get('is_active', 'true').lower() == 'true'

        # Проверяем, что хотя бы один параметр передан
        if not any([last_name, first_name, middle_name, club_id]):
            return jsonify({
                'success': False,
                'message': 'Укажите хотя бы один параметр поиска (last_name, first_name, middle_name или club_id)'
            }), 400

        name_query = {
            'last_name': last_name,
            'first_name': first_name,
            'middle_name': middle_name
        }

        athletes = athlete_repo.search_athletes_by_name(name_query, club_id)
        result = []

        for athlete in athletes:
            result.append({
                'id': athlete.id,
                'user_id': athlete.user_id,
                'last_name': athlete.user.last_name,
                'first_name': athlete.user.first_name,
                'middle_name': athlete.user.middle_name,
                'birth_date': athlete.birth_date.isoformat() if athlete.birth_date else None,
                'age': athlete.age,
                'gender': athlete.gender,
                'club_id': athlete.club_id,
                'club_name': athlete.club.name if athlete.club else None,
                'rank': athlete.rank.level if athlete.rank else None,
                'license_number': athlete.license_number,
                'is_active': athlete.is_active
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при поиске участника: {str(e)}'
        }), 500