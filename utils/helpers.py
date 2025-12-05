"""
Вспомогательные функции для системы
"""

from datetime import datetime, timedelta
import math

def format_duration(seconds):
    """
    Форматирование длительности в читаемый вид
    """
    if not seconds:
        return "0:00"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def format_weight(weight):
    """
    Форматирование веса
    """
    if not weight:
        return "—"
    return f"{weight} кг"

def get_age_category(birth_date, categories_config):
    """
    Определение возрастной категории по дате рождения
    """
    if not birth_date:
        return None

    today = datetime.today().date()
    age = today.year - birth_date.year

    # Корректировка если день рождения еще не наступил в этом году
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1

    for category, (min_age, max_age) in categories_config.items():
        if min_age <= age <= max_age:
            return category

    return None

def calculate_rounds(participants_count):
    """
    Расчет количества раундов для сетки
    """
    if participants_count <= 0:
        return 0

    return math.ceil(math.log2(participants_count))

def calculate_fights_count(participants_count, bracket_type='SINGLE_ELIMINATION'):
    """
    Расчет общего количества схваток
    """
    if bracket_type == 'SINGLE_ELIMINATION':
        return participants_count - 1
    elif bracket_type == 'DOUBLE_ELIMINATION':
        return (participants_count * 2) - 2
    else:  # ROUND_ROBIN
        return (participants_count * (participants_count - 1)) // 2

def generate_bracket_positions(participants_count):
    """
    Генерация позиций в сетке
    """
    if participants_count <= 1:
        return [1]

    # Ближайшая степень двойки
    next_power = 2 ** math.ceil(math.log2(participants_count))

    positions = []
    for i in range(participants_count):
        # Алгоритм seeding для равномерного распределения сильных участников
        pos = ((i * 2) % next_power) + ((i * 2) // next_power) + 1
        positions.append(pos)

    return positions[:participants_count]

def calculate_ranking_points(victory_type, fight_duration=0):
    """
    Расчет рейтинговых очков за победу
    """
    from .constants import VICTORY_POINTS

    base_points = VICTORY_POINTS.get(victory_type, 0)

    # Бонус за быструю победу
    time_bonus = 0
    if fight_duration > 0 and fight_duration < 60:  # Меньше минуты
        time_bonus = 10
    elif fight_duration > 0 and fight_duration < 120:  # Меньше двух минут
        time_bonus = 5

    return base_points + time_bonus

def format_penalties(penalties_string):
    """
    Форматирование штрафов для отображения
    """
    if not penalties_string:
        return []

    penalties = penalties_string.split(',')
    formatted = []

    for penalty in penalties:
        if penalty == 'SHIDO':
            formatted.append('Шидо')
        elif penalty == 'HANSOKU_MAKE':
            formatted.append('Хансоку-маке')
        else:
            formatted.append(penalty)

    return formatted

def get_technique_category(technique_name):
    """
    Определение категории техники
    """
    from .constants import TECHNIQUES

    for category, techniques in TECHNIQUES.items():
        for subcategory, tech_list in techniques.items():
            if technique_name in tech_list:
                return f"{category} - {subcategory}"

    return "Другая техника"

def schedule_fights(fights, tatami_count, start_time, break_duration=300):
    """
    Планирование расписания схваток по татами
    """
    if not fights:
        return []

    # Сортируем схватки по важности (финалы в конец)
    fights.sort(key=lambda f: f.round_number)

    scheduled_fights = []
    current_time = start_time
    tatami_schedules = {i: current_time for i in range(1, tatami_count + 1)}

    for fight in fights:
        # Находим татами с самым ранним доступным временем
        available_tatami = min(tatami_schedules.items(), key=lambda x: x[1])[0]
        fight_time = tatami_schedules[available_tatami]

        # Назначаем схватку
        fight.tatami = available_tatami
        fight.scheduled_time = fight_time
        scheduled_fights.append(fight)

        # Обновляем время для татами (схватка + перерыв)
        tatami_schedules[available_tatami] = fight_time + timedelta(
            seconds=fight.tournament.fight_duration + break_duration
        )

    return scheduled_fights

def export_data(data, format_type):
    """
    Экспорт данных в различных форматах
    """
    if format_type == 'JSON':
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)

    elif format_type == 'CSV':
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        if data and len(data) > 0:
            # Заголовки
            writer.writerow(data[0].keys())
            # Данные
            for row in data:
                writer.writerow(row.values())

        return output.getvalue()

    else:
        return str(data)

def validate_license_number(license_number):
    """
    Валидация номера лицензии
    """
    if not license_number:
        return True

    import re
    # Простая проверка формата: буквы и цифры, длина 6-20 символов
    pattern = r'^[A-Z0-9]{6,20}$'
    return bool(re.match(pattern, license_number.upper()))