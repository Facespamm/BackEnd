"""
pdf_routes.py
Blueprint для генерации PDF результатов турнира.

Подключить в app.py:
    from pdf_routes import pdf_bp
    app.register_blueprint(pdf_bp)
"""

from flask import Blueprint, send_file, jsonify, request
import io

from database.db import create_session
from repository.tournament_repo import TournamentRepository
from repository.category_repo import CategoryRepository
from repository.figth_repo import FightRepository
from repository.result_repo import ResultRepository
from repository.athlete_repo import AthleteRepository
from new_model.Enums import BracketType
from services.pdf_generator import generate_tournament_pdf

pdf_bp = Blueprint('pdf', __name__, url_prefix='/api/pdf')


# ─────────────────────────────────────────────────────────────
# Хелпер: собрать пьедестал категории из результатов
# ─────────────────────────────────────────────────────────────
def _build_podium(fights, results_map, athlete_repo):
    """
    Строим пьедестал на основе боёв и результатов.
    Логика IJF:
      1-е место  — победитель финала
      2-е место  — проигравший финала
      3-е место  — победители утешительных финалов (или полуфиналисты)
      5, 7 место — остальные по вылету
    """
    podium = []

    # Находим финал — бой с максимальным round_number среди MAIN
    main_fights = [f for f in fights if not f.get('type_bracket') or f.get('type_bracket') == 'MAIN']
    if not main_fights:
        return podium

    max_round = max((f.get('round') or f.get('round_number', 1)) for f in main_fights)
    final_fights = [f for f in main_fights if (f.get('round') or f.get('round_number', 1)) == max_round]

    if not final_fights:
        return podium

    final = final_fights[0]
    result = results_map.get(final['id'])

    if result:
        winner_id = result.get('winner_id')
        white_id  = (final.get('white_athlete') or {}).get('id')
        blue_id   = (final.get('blue_athlete')  or {}).get('id')
        loser_id  = blue_id if winner_id == white_id else white_id

        def get_ath(athlete_id):
            if not athlete_id:
                return {}
            data = athlete_repo.get_athlete_name_data(athlete_id)
            if data:
                data['id'] = athlete_id
            return data or {}

        def get_club(athlete_id):
            try:
                ath = athlete_repo.get_athlete_by_id(athlete_id)
                return ath.club.name if ath and ath.club else '—'
            except Exception:
                return '—'

        if winner_id:
            podium.append({'pos': 1, 'athlete': get_ath(winner_id), 'club': get_club(winner_id)})
        if loser_id:
            podium.append({'pos': 2, 'athlete': get_ath(loser_id),  'club': get_club(loser_id)})

    # 3-е место — победители утешительных финальных боёв
    cons_final_types = [
        str(BracketType.FINALIST_CONSOLATION_GROUP_A),
        str(BracketType.FINALIST_CONSOLATION_GROUP_B),
    ]
    cons_finals = [
        f for f in fights
        if str(f.get('type_bracket', '')) in cons_final_types
    ]

    # Берём последний бой каждой группы (максимальный fight_number)
    for group_type in cons_final_types:
        group_fights = sorted(
            [f for f in cons_finals if str(f.get('type_bracket', '')) == group_type],
            key=lambda x: x.get('fight_number') or 0
        )
        if not group_fights:
            continue
        last_fight = group_fights[-1]
        res = results_map.get(last_fight['id'])
        if res:
            winner_id = res.get('winner_id')
            if winner_id:
                data = athlete_repo.get_athlete_name_data(winner_id)
                if data:
                    data['id'] = winner_id
                podium.append({
                    'pos': 3,
                    'athlete': data or {},
                    'club': get_club(winner_id)
                })

    return sorted(podium, key=lambda x: (x['pos'], 0))


# ─────────────────────────────────────────────────────────────
# Endpoint: GET /api/pdf/tournament/<tournament_id>
# ─────────────────────────────────────────────────────────────
@pdf_bp.route('/tournament/<int:tournament_id>', methods=['GET'])
def get_tournament_pdf(tournament_id):
    """
    Генерирует PDF с турнирной сеткой, утешительными боями и результатами.

    Query params:
        category_id (int, optional) — если передан, генерирует PDF только для одной категории
    """
    try:
        category_id = request.args.get('category_id', type=int)

        with create_session() as session:
            # ── Турнир ──
            tournament_repo = TournamentRepository(session)
            tournament = tournament_repo.get_tournament_by_id(tournament_id)
            if not tournament:
                return jsonify({'success': False, 'message': 'Турнир не найден'}), 404

            # ── Категории ──
            category_repo = CategoryRepository(session)
            fight_repo    = FightRepository(session)
            result_repo   = ResultRepository(session)
            athlete_repo  = AthleteRepository(session)

            # Получаем tournament_categories
            tc_list = tournament_repo.get_tournament_categories(tournament_id)
            if not tc_list:
                return jsonify({'success': False, 'message': 'Категории не найдены'}), 404

            # Фильтр по категории если нужно
            if category_id:
                tc_list = [tc for tc in tc_list if tc.category_id == category_id]
                if not tc_list:
                    return jsonify({'success': False, 'message': 'Категория не найдена'}), 404

            categories_data = []

            for tc in tc_list:
                cat = category_repo.get_category_by_id(tc.category_id)
                if not cat:
                    continue

                tc_id = tc.tournament_category_id

                # Все бои категории
                all_fights_orm = fight_repo.get_all_fights_by_tournament_category(tc_id)

                fights_dto = []
                for f in all_fights_orm:
                    fights_dto.append({
                        'id':            f.id,
                        'round':         f.round_number,
                        'fight_number':  f.fight_number,
                        'type_bracket':  f.type_bracket.value if f.type_bracket else 'MAIN',
                        'white_athlete': athlete_repo.get_athlete_by_fight(f.white_athlete_id, f.id),
                        'blue_athlete':  athlete_repo.get_athlete_by_fight(f.blue_athlete_id, f.id),
                    })

                # Результаты
                results_orm = result_repo.get_results_by_tournament(tournament_id, tc.category_id)
                results_dto = []
                results_map = {}
                for r in results_orm:
                    dto = {
                        'fight_id':       r.fight_id,
                        'winner_id':      r.winner_id,
                        'victory_type':   r.victory_type.value if r.victory_type else '',
                        'fight_duration': r.fight_duration,
                    }
                    results_dto.append(dto)
                    results_map[r.fight_id] = dto

                # Пьедестал
                podium = _build_podium(fights_dto, results_map, athlete_repo)

                # Количество участников
                competitors = len(set(
                    f.get('id') for f in
                    [f.get('white_athlete') or {} for f in fights_dto] +
                    [f.get('blue_athlete')  or {} for f in fights_dto]
                    if f.get('id')
                ))

                categories_data.append({
                    'id':          cat.id,
                    'name':        cat.name,
                    'tatami':      tc.tatami_number if hasattr(tc, 'tatami_number') else '—',
                    'competitors': competitors,
                    'fights':      fights_dto,
                    'results':     results_dto,
                    'podium':      podium,
                })

            if not categories_data:
                return jsonify({'success': False, 'message': 'Нет данных для генерации PDF'}), 404

            # ── Собираем данные для генератора ──
            tournament_payload = {
                'tournament': {
                    'id':         tournament.id,
                    'name':       tournament.name,
                    'start_date': str(tournament.start_date) if tournament.start_date else '',
                    'city':       tournament.city or '',
                    'country':    tournament.country or '',
                },
                'categories': categories_data,
            }

        # ── Генерируем PDF (вне сессии) ──
        pdf_bytes = generate_tournament_pdf(tournament_payload)

        filename = f"tournament_{tournament_id}.pdf"
        if category_id:
            filename = f"tournament_{tournament_id}_cat_{category_id}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Ошибка генерации PDF: {str(e)}'
        }), 500