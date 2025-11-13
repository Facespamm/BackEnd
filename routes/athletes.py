"""
Маршруты для управления участниками
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from utils.security import admin_required
from models.athlete import Athlete
from models.club import Club
from database.db import db

athletes_bp = Blueprint('athletes', __name__)

@athletes_bp.route('/')
@admin_required
def list_athletes():
    """Список участников"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Фильтры
    club_id = request.args.get('club_id', type=int)
    search = request.args.get('search', '')

    query = Athlete.query.filter_by(is_active=True)

    if club_id:
        query = query.filter_by(club_id=club_id)

    if search:
        query = query.filter(
            db.or_(
                Athlete.last_name.ilike(f'%{search}%'),
                Athlete.first_name.ilike(f'%{search}%'),
                Athlete.license_number.ilike(f'%{search}%')
            )
        )

    athletes = query.order_by(Athlete.last_name, Athlete.first_name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    clubs = Club.query.filter_by(is_active=True).order_by(Club.name).all()

    return render_template(
        'admin/athletes/list.html',
        athletes=athletes,
        clubs=clubs,
        club_id=club_id,
        search=search
    )

@athletes_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_athlete():
    """Добавление участника"""
    from utils.forms import AthleteForm
    from utils.validators import validate_athlete_data

    form = AthleteForm()

    # Заполняем выбор клубов
    form.club_id.choices = [(0, '-- Выберите клуб --')] + [
        (club.id, club.name) for club in Club.query.filter_by(is_active=True).order_by(Club.name).all()
    ]

    if form.validate_on_submit():
        # Валидация данных
        errors = validate_athlete_data(request.form)

        if errors:
            for error in errors:
                flash(error, 'danger')
        else:
            # Создание участника
            athlete = Athlete(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                middle_name=form.middle_name.data,
                birth_date=form.birth_date.data,
                gender=form.gender.data,
                club_id=form.club_id.data if form.club_id.data != 0 else None,
                rank=form.rank.data,
                license_number=form.license_number.data,
                phone=form.phone.data,
                email=form.email.data,
                medical_check=form.medical_check.data,
                insurance_number=form.insurance_number.data
            )

            if athlete.save():
                flash(f'Участник {athlete.full_name} успешно создан', 'success')
                return redirect(url_for('athletes.list_athletes'))
            else:
                flash('Ошибка при создании участника', 'danger')

    return render_template('admin/athletes/add.html', form=form)

@athletes_bp.route('/<int:athlete_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_athlete(athlete_id):
    """Редактирование участника"""
    from utils.forms import AthleteForm

    athlete = Athlete.query.get_or_404(athlete_id)
    form = AthleteForm(obj=athlete)

    # Заполняем выбор клубов
    form.club_id.choices = [(0, '-- Выберите клуб --')] + [
        (club.id, club.name) for club in Club.query.filter_by(is_active=True).order_by(Club.name).all()
    ]

    if form.validate_on_submit():
        form.populate_obj(athlete)

        if athlete.save():
            flash('Участник успешно обновлен', 'success')
            return redirect(url_for('athletes.list_athletes'))
        else:
            flash('Ошибка при обновлении участника', 'danger')

    return render_template('admin/athletes/edit.html', form=form, athlete=athlete)

@athletes_bp.route('/<int:athlete_id>/delete', methods=['POST'])
@admin_required
def delete_athlete(athlete_id):
    """Удаление участника"""
    athlete = Athlete.query.get_or_404(athlete_id)
    athlete.is_active = False

    if athlete.save():
        flash('Участник успешно удален', 'success')
    else:
        flash('Ошибка при удалении участника', 'danger')

    return redirect(url_for('athletes.list_athletes'))

@athletes_bp.route('/<int:athlete_id>/profile')
@admin_required
def athlete_profile(athlete_id):
    """Профиль участника"""
    athlete = Athlete.query.get_or_404(athlete_id)

    # Статистика участника
    from services.ranking_service import RankingService
    ranking_service = RankingService()
    stats = ranking_service._get_athlete_stats(athlete)

    # История выступлений
    from models.fight import Fight
    fights = Fight.query.filter(
        ((Fight.white_athlete_id == athlete_id) | (Fight.blue_athlete_id == athlete_id)) &
        (Fight.status == 'COMPLETED')
    ).order_by(Fight.created_at.desc()).limit(10).all()

    return render_template(
        'admin/athletes/profile.html',
        athlete=athlete,
        stats=stats,
        fights=fights
    )

@athletes_bp.route('/import', methods=['GET', 'POST'])
@admin_required
def import_athletes():
    """Импорт участников из файла"""
    if request.method == 'POST':
        # Здесь будет логика импорта из CSV/Excel
        flash('Функция импорта в разработке', 'info')
        return redirect(url_for('athletes.list_athletes'))

    return render_template('admin/athletes/import.html')

@athletes_bp.route('/export')
@admin_required
def export_athletes():
    """Экспорт участников"""
    from services.export_service import ExportService

    format_type = request.args.get('format', 'CSV')
    export_service = ExportService()

    athletes_data = []
    athletes = Athlete.query.filter_by(is_active=True).order_by(Athlete.last_name).all()

    for athlete in athletes:
        athletes_data.append({
            'id': athlete.id,
            'last_name': athlete.last_name,
            'first_name': athlete.first_name,
            'middle_name': athlete.middle_name or '',
            'birth_date': athlete.birth_date.strftime('%Y-%m-%d'),
            'gender': athlete.gender,
            'club': athlete.club.name if athlete.club else '',
            'rank': athlete.rank or '',
            'license_number': athlete.license_number or '',
            'phone': athlete.phone or '',
            'email': athlete.email or ''
        })

    export_content = export_service._export_csv(athletes_data)

    from flask import Response
    response = Response(export_content, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=athletes.csv'

    return response

@athletes_bp.route('/api/search')
@admin_required
def api_search_athletes():
    """API поиска участников (для автодополнения)"""
    query = request.args.get('q', '')

    if len(query) < 2:
        return jsonify([])

    athletes = Athlete.query.filter(
        db.or_(
            Athlete.last_name.ilike(f'%{query}%'),
            Athlete.first_name.ilike(f'%{query}%')
        )
    ).filter_by(is_active=True).limit(10).all()

    results = []
    for athlete in athletes:
        results.append({
            'id': athlete.id,
            'text': f"{athlete.full_name} ({athlete.club.name if athlete.club else 'без клуба'})"
        })

    return jsonify(results)