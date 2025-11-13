"""
Маршруты для управления взвешиванием
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from utils.security import admin_required
from models.tournament import Tournament
from models.weighing import Weighing
from models.athlete import Athlete
from database.db import db

weighing_bp = Blueprint('weighing', __name__)

@weighing_bp.route('/<int:tournament_id>')
@admin_required
def weighing_session(tournament_id):
    """Сессия взвешивания"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Получаем всех участников турнира
    all_athletes = []
    for category in tournament.categories:
        all_athletes.extend(category.athletes)

    # Получаем взвешивания
    weighings = Weighing.query.filter_by(tournament_id=tournament_id).all()
    weighed_athlete_ids = [w.athlete_id for w in weighings]

    # Разделяем на взвешенных и невзвешенных
    weighed_athletes = [a for a in all_athletes if a.id in weighed_athlete_ids]
    not_weighed_athletes = [a for a in all_athletes if a.id not in weighed_athlete_ids]

    # Статистика взвешивания
    stats = {
        'total_athletes': len(all_athletes),
        'weighed': len(weighed_athletes),
        'not_weighed': len(not_weighed_athletes),
        'valid_weighings': len([w for w in weighings if w.is_valid]),
        'invalid_weighings': len([w for w in weighings if not w.is_valid])
    }

    return render_template(
        'admin/weighing/session.html',
        tournament=tournament,
        weighed_athletes=weighed_athletes,
        not_weighed_athletes=not_weighed_athletes,
        stats=stats,
        weighings=weighings
    )

@weighing_bp.route('/<int:tournament_id>/weigh', methods=['POST'])
@admin_required
def weigh_athlete(tournament_id):
    """Взвешивание участника"""
    tournament = Tournament.query.get_or_404(tournament_id)
    athlete_id = request.form.get('athlete_id')
    weight = request.form.get('weight')
    notes = request.form.get('notes', '')

    if not athlete_id or not weight:
        flash('Необходимо указать участника и вес', 'danger')
        return redirect(url_for('weighing.weighing_session', tournament_id=tournament_id))

    try:
        weight_float = float(weight)
        if weight_float < 20 or weight_float > 200:
            flash('Вес должен быть от 20 до 200 кг', 'danger')
            return redirect(url_for('weighing.weighing_session', tournament_id=tournament_id))
    except ValueError:
        flash('Неверный формат веса', 'danger')
        return redirect(url_for('weighing.weighing_session', tournament_id=tournament_id))

    athlete = Athlete.query.get(athlete_id)
    if not athlete:
        flash('Участник не найден', 'danger')
        return redirect(url_for('weighing.weighing_session', tournament_id=tournament_id))

    # Регистрируем взвешивание
    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    if weighing_service.register_weighing(athlete_id, weight_float, notes):
        flash(f'Участник {athlete.full_name} взвешен: {weight} кг', 'success')
    else:
        flash('Ошибка при регистрации взвешивания', 'danger')

    return redirect(url_for('weighing.weighing_session', tournament_id=tournament_id))

@weighing_bp.route('/<int:tournament_id>/results')
@admin_required
def weighing_results(tournament_id):
    """Результаты взвешивания"""
    tournament = Tournament.query.get_or_404(tournament_id)

    # Получаем все взвешивания
    weighings = Weighing.query.filter_by(tournament_id=tournament_id).order_by(
        Weighing.weighing_time.desc()
    ).all()

    # Статистика
    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)
    stats = weighing_service.get_weighing_statistics()

    return render_template(
        'admin/weighing/results.html',
        tournament=tournament,
        weighings=weighings,
        stats=stats
    )

@weighing_bp.route('/<int:tournament_id>/assign_categories')
@admin_required
def assign_categories(tournament_id):
    """Автоматическое распределение по категориям"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    result = weighing_service.assign_to_categories()

    if result['assigned_count'] > 0:
        flash(f'Успешно распределено {result["assigned_count"]} участников по категориям', 'success')
    else:
        flash('Не удалось распределить участников по категориям', 'warning')

    if result['errors']:
        for error in result['errors']:
            flash(error, 'danger')

    return redirect(url_for('weighing.weighing_results', tournament_id=tournament_id))

@weighing_bp.route('/<int:tournament_id>/validate/<int:weighing_id>', methods=['POST'])
@admin_required
def validate_weighing(tournament_id, weighing_id):
    """Валидация взвешивания"""
    weighing = Weighing.query.get_or_404(weighing_id)
    is_valid = request.form.get('is_valid') == 'true'

    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    if weighing_service.validate_weighing(weighing_id, is_valid):
        status = 'валидным' if is_valid else 'невалидным'
        flash(f'Взвешивание отмечено как {status}', 'success')
    else:
        flash('Ошибка при валидации взвешивания', 'danger')

    return redirect(url_for('weighing.weighing_results', tournament_id=tournament_id))

@weighing_bp.route('/<int:tournament_id>/without_weighing')
@admin_required
def without_weighing(tournament_id):
    """Участники без взвешивания"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    athletes_without_weighing = weighing_service.get_athletes_without_weighing()

    return render_template(
        'admin/weighing/without_weighing.html',
        tournament=tournament,
        athletes=athletes_without_weighing
    )

@weighing_bp.route('/<int:tournament_id>/export')
@admin_required
def export_weighing_data(tournament_id):
    """Экспорт данных взвешивания"""
    tournament = Tournament.query.get_or_404(tournament_id)

    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    format_type = request.args.get('format', 'CSV')
    export_content = weighing_service.export_weighing_data(format_type)

    from flask import Response

    if format_type == 'JSON':
        response = Response(export_content, mimetype='application/json')
        response.headers['Content-Disposition'] = f'attachment; filename=weighing_{tournament_id}.json'
    else:  # CSV
        response = Response(export_content, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=weighing_{tournament_id}.csv'

    return response

@weighing_bp.route('/<int:tournament_id>/api/weighing_stats')
@admin_required
def api_weighing_stats(tournament_id):
    """API статистики взвешивания"""
    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    stats = weighing_service.get_weighing_statistics()
    return jsonify(stats)

@weighing_bp.route('/<int:tournament_id>/api/category_suggestions/<int:athlete_id>')
@admin_required
def api_category_suggestions(tournament_id, athlete_id):
    """API предложений по категориям"""
    from services.weighing_service import WeighingService
    weighing_service = WeighingService(tournament_id)

    suggestions = weighing_service.get_category_suggestions(athlete_id)
    return jsonify(suggestions)