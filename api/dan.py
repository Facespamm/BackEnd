from flask import Blueprint, request, jsonify
from flasgger import swag_from

from new_model.handbook.new_dan import DanNew
from repository.dan_repo import DanRepository

dans_bp = Blueprint('dans', __name__, url_prefix='/api/dans')
dan_repo = DanRepository()

@dans_bp.route('/', methods=['GET'])
def get_dans():
    """Получить список данов"""
    try:
        dans = dan_repo.get_dans()

        result = []
        for dan in dans:
            result.append({
                'id': dan.id,
                'level': dan.level,
                'description': dan.description,
                'athletes_count': dan_repo.get_athletes_count(dan.id)
            })

        return jsonify({
            'success': True,
            'dans': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении данов: {str(e)}'
        }), 500


@dans_bp.route('/', methods=['POST'])
def create_dan():
    """Создать новый дан"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Не передан JSON"}), 400

        if not data.get('level'):
            return jsonify({"success": False, "message": "Уровень дана обязателен"}), 400

        existing_dan = dan_repo.get_dan_by_name(data['level'].strip())
        if existing_dan:
            return jsonify({"success": False, "message": "Дан с таким уровнем уже существует"}), 400

        dan = DanNew(
            level=data['level'].strip(),
            description=data.get('description')
        )

        dan_id = dan_repo.create_dan(dan)
        if dan_id:
            return jsonify({
                "success": True,
                "message": "Дан успешно создан",
                "dan_id": dan_id
            }), 201
        else:
            return jsonify({"success": False, "message": "Ошибка при сохранении в базу"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": f"Ошибка сервера: {str(e)}"}), 500