from flask import Blueprint, request, jsonify

from new_model.Enums import translate_gender
from new_model.handbook.category_new import CategoryNew
from repository.category_repo import CategoryRepository

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')
category_repo = CategoryRepository()

@categories_bp.route('/', methods=['GET'])
def get_categories():
    """Получить список категорий"""
    try:
        tournament_id = request.args.get('tournament_id', type=int)

        categories =category_repo.get_categories(tournament_id)

        result = []
        for category in categories:
            tournament_ids = [t.tournament_category_id for t in category.tournament_categories]

            result.append({
                'id': category.id,
                'name': category.name,
                'gender': category.gender.value,
                'min_weight': category.min_weight,
                'max_weight': category.max_weight,
                'min_age': category.min_year,
                'max_age': category.max_year,
                'athletes_count': category_repo.get_all_athletes(category.id),
                'tournament_id': tournament_ids
            })

        return jsonify({
            'success': True,
            'categories': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении категорий: {str(e)}'
        }), 500

@categories_bp.route('/', methods=['POST'])
def create_category():
    """Создать новую категорию"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        if not data.get('name') or not data.get('gender'):
            return jsonify({
                'success': False,
                'message': 'Обязательные поля: name, tournament_id, gender'
            }), 400

        translate_gender_ =  translate_gender(data['gender'])
        category = CategoryNew(
            name=data['name'],
            gender=translate_gender_,
            min_weight=data.get('min_weight'),
            max_weight=data.get('max_weight'),
            min_year=data.get('min_age'),
            max_year=data.get('max_age')
        )

        is_create = category_repo.create_category(category)

        if is_create:
            return jsonify({
                'success': True,
                'message': 'Категория успешно создана',
                'category_id': category.id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при сохранении категории'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при создании категории: {str(e)}'
        }), 500

@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """Получить информацию о категории"""
    try:
        category = category_repo.get_category_by_id(category_id)

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        return jsonify({
            'id': category.id,
            'name': category.name,
            'gender': category.gender.value,
            'min_weight': category.min_weight,
            'max_weight': category.max_weight,
            'min_age': category.min_age,
            'max_age': category.max_age,
            'athletes_count': category_repo.get_all_athletes(category.id),
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении категории: {str(e)}'
        }), 500

@categories_bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Обновить категорию"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'Не передан JSON'
            }), 400

        list_of_fields = ['name', 'min_weight', 'max_weight', 'min_age', 'max_age']
        for field in list_of_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Поле {field} обязательно'}), 400

        is_update = category_repo.update_category(category_id, data)

        if is_update:
            return jsonify({
                'success': True,
                'message': 'Категория успешно обновлена',
                'category_id': category_id
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при обновлении категории'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при обновлении категории: {str(e)}'
        }), 500


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Удалить категорию"""
    try:
        category = category_repo.get_category_by_id(category_id)

        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        is_delete = category_repo.delete_category(category)

        if is_delete:
            return jsonify({
                'success': True,
                'message': 'Категория удалена'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при удалении категории'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при удалении категории: {str(e)}'
        }), 500


@categories_bp.route('/<int:category_id>/athletes', methods=['GET'])
def get_category_athletes(category_id):
    """Получить участников категории"""
    try:
        category = category_repo.get_category_by_id(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': 'Категория не найдена'
            }), 404

        athletes = []
        for athlete in category.athletes:
            athletes.append({
                'id': athlete.id,
                'full_name': athlete.name,
                'club': athlete.club_id,
                'age': athlete.age,
                'rank': athlete.rank_id
            })

        return jsonify({
            'success': True,
            'category': category.name,
            'athletes': athletes,
            'total': len(athletes)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении участников категории: {str(e)}'
        }), 500