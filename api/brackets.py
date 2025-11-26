from flask import request, Blueprint, jsonify
from models.bracket import Bracket
from services.bracket_generator import BracketGenerator

brackets_bp = Blueprint('brackets', __name__, url_prefix='/api/brackets')


@brackets_bp.route('/', methods=['GET'])
def get_brackets_list():
    """Получить список сеток
    ---
    tags:
      - Brackets
    parameters:
      - name: tournament_id
        in: query
        type: integer
        required: false
        description: ID турнира
      - name: category_id
        in: query
        type: integer
        required: false
        description: ID категории
    responses:
      200:
        description: Список сеток успешно получен
        schema:
          type: object
          properties:
            success:
              type: boolean
            brackets:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  bracket_type:
                    type: string
                  status:
                    type: string
                  tournament_id:
                    type: integer
                  category_id:
                    type: integer
                  progress_percentage:
                    type: number
                  athletes_count:
                    type: integer
            total:
              type: integer
      500:
        description: Ошибка сервера
    """
    try:
        tournament_id = request.args.get('tournament_id', type=int)
        category_id = request.args.get('category_id', type=int)

        query = Bracket.query

        if tournament_id:
            query = query.filter_by(tournament_id=tournament_id)
        if category_id:
            query = query.filter_by(category_id=category_id)

        brackets = query.all()

        result = []
        for bracket in brackets:
            result.append({
                'id': bracket.id,
                'name': bracket.name,
                'bracket_type': bracket.bracket_type,
                'status': bracket.status,
                'tournament_id': bracket.tournament_id,
                'category_id': bracket.category_id,
                'progress_percentage': bracket.progress_percentage,
                'athletes_count': bracket.athletes_count
            })

        return jsonify({
            'success': True,
            'brackets': result,
            'total': len(result)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении сеток: {str(e)}'
        }), 500


@brackets_bp.route('/<int:bracket_id>/generate', methods=['POST'])
def generate_bracket(bracket_id):
    """Сгенерировать схватки для сетки
    ---
    tags:
      - Brackets
    parameters:
      - name: bracket_id
        in: path
        type: integer
        required: true
        description: ID сетки
    responses:
      200:
        description: Сетка успешно сгенерирована
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            fights_count:
              type: integer
      400:
        description: Недостаточно участников или ошибка генерации
      404:
        description: Сетка не найдена
      500:
        description: Ошибка сервера
    """
    try:
        bracket = Bracket.query.get(bracket_id)
        if not bracket:
            return jsonify({'success': False, 'message': 'Сетка не найдена'}), 404

        if bracket.athletes_count < 2:
            return jsonify({'success': False, 'message': 'Для генерации сетки нужно минимум 2 участника'}), 400

        generator = BracketGenerator(bracket)
        fights = generator.generate()

        if fights:
            return jsonify({
                'success': True,
                'message': f'Сетка успешно сгенерирована. Создано {len(fights)} схваток.',
                'fights_count': len(fights)
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Ошибка при генерации сетки'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при генерации сетки: {str(e)}'}), 500

@brackets_bp.route('/', methods=['POST'])
def create_bracket():
    """Создать новую сетку
    ---
    tags:
      - Brackets
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
            - tournament_id
            - category_id
          properties:
            name:
              type: string
              example: "Мужчины -73 кг"
            tournament_id:
              type: integer
            category_id:
              type: integer
            bracket_type:
              type: string
              enum: ['single_elimination', 'double_elimination']
              default: 'single_elimination'
            has_consolation:
              type: boolean
              default: false
    responses:
      201:
        description: Сетка успешно создана
      400:
        description: Неверные данные
      404:
        description: Турнир или категория не найдены
      500:
        description: Ошибка сервера
    """
    try:
        data = request.get_json()
        if not data or not data.get('name') or not data.get('tournament_id') or not data.get('category_id'):
            return jsonify({'success': False, 'message': 'Отсутствуют обязательные поля'}), 400

        from models.tournament import Tournament
        from models.category import Category

        tournament = Tournament.query.get(data['tournament_id'])
        category = Category.query.get(data['category_id'])

        if not tournament or not category:
            return jsonify({'success': False, 'message': 'Турнир или категория не найдены'}), 404

        bracket = Bracket(
            name=data['name'],
            tournament_id=data['tournament_id'],
            category_id=data['category_id'],
            bracket_type=data.get('bracket_type', 'single_elimination'),
            has_consolation=data.get('has_consolation', False),
            status='DRAFT',
        )
        bracket.save_to_db()

        return jsonify({
            'success': True,
            'message': 'Сетка успешно создана',
            'bracket_id': bracket.id
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка создания сетки: {str(e)}'}), 500

@brackets_bp.route('/<int:bracket_id>/fights', methods=['GET'])
def get_bracket_fights(bracket_id):
    """Получить схватки сетки
    ---
    tags:
      - Brackets
    parameters:
      - name: bracket_id
        in: path
        type: integer
        required: true
        description: ID сетки
    responses:
      200:
        description: Схватки успешно получены
        schema:
          type: object
          properties:
            success:
              type: boolean
            bracket:
              type: string
            fights_by_round:
              type: object
              additionalProperties:
                type: array
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    fight_number:
                      type: integer
                    status:
                      type: string
                    white_athlete:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                    blue_athlete:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
                    winner:
                      type: object
                      properties:
                        id:
                          type: integer
                        name:
                          type: string
      404:
        description: Сетка не найдена
      500:
        description: Ошибка сервера
    """
    try:
        bracket = Bracket.query.get(bracket_id)
        if not bracket:
            return jsonify({'success': False, 'message': 'Сетка не найдена'}), 404

        fights_by_round = {}
        for fight in bracket.fights:
            round_num = fight.round_number
            if round_num not in fights_by_round:
                fights_by_round[round_num] = []

            fight_data = {
                'id': fight.id,
                'fight_number': fight.fight_number,
                'status': fight.status,
                'white_athlete': None,
                'blue_athlete': None,
                'winner': None
            }

            if fight.white_athlete:
                fight_data['white_athlete'] = {
                    'id': fight.white_athlete.id,
                    'name': fight.white_athlete.full_name
                }

            if fight.blue_athlete:
                fight_data['blue_athlete'] = {
                    'id': fight.blue_athlete.id,
                    'name': fight.blue_athlete.full_name
                }

            if fight.result and fight.result.winner:
                fight_data['winner'] = {
                    'id': fight.result.winner_id,
                    'name': fight.result.winner.full_name
                }

            fights_by_round[round_num].append(fight_data)

        return jsonify({
            'success': True,
            'bracket': bracket.name,
            'fights_by_round': fights_by_round
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка при получении схваток сетки: {str(e)}'
        }), 500