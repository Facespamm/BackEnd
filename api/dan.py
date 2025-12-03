from flask import Blueprint, request, jsonify
from flasgger import swag_from
from models.Dan import Dan

dans_bp = Blueprint('dans', __name__, url_prefix='/dans')


@dans_bp.route('/', methods=['GET'])
@swag_from({
    'tags': ['Dans'],
    'summary': 'Получить список данов',
    'description': 'Возвращает список всех уровней данов',
    'responses': {
        200: {
            'description': 'Список данов получен успешно',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'dans': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'level': {'type': 'string'},
                                'description': {'type': 'string'},
                                'athletes_count': {'type': 'integer'}
                            }
                        }
                    },
                    'total': {'type': 'integer'}
                }
            }
        },
        500: {
            'description': 'Ошибка сервера'
        }
    }
})
def get_dans():
    """Получить список данов"""
    try:
        dans = Dan.query.order_by(Dan.level).all()

        result = []
        for dan in dans:
            result.append({
                'id': dan.id,
                'level': dan.level,
                'description': dan.description,
                'athletes_count': dan.athletes.count() if dan.athletes else 0
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
@swag_from({
    "tags": ["Dans"],
    "summary": "Создать новый дан",
    "description": "Добавляет новый уровень дана в систему",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "required": ["level"],
                "properties": {
                    "level": {"type": "string", "example": "1 дан"},
                    "description": {"type": "string", "example": "Первый уровень мастерства"}
                }
            }
        }
    ],
    "responses": {
        201: {
            "description": "Дан успешно создан",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "dan_id": {"type": "integer"}
                }
            }
        },
        400: {"description": "Ошибка валидации или дан уже существует"}
    }
})
def create_dan():
    """Создать новый дан"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "message": "Не передан JSON"}), 400

        if not data.get('level'):
            return jsonify({"success": False, "message": "Уровень дана обязателен"}), 400

        if Dan.query.filter_by(level=data['level'].strip()).first():
            return jsonify({"success": False, "message": "Дан с таким уровнем уже существует"}), 400

        dan = Dan(
            level=data['level'].strip(),
            description=data.get('description')
        )

        if dan.save_to_db():
            return jsonify({
                "success": True,
                "message": "Дан успешно создан",
                "dan_id": dan.id
            }), 201
        else:
            return jsonify({"success": False, "message": "Ошибка при сохранении в базу"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": f"Ошибка сервера: {str(e)}"}), 500