from config import USER_ROLES
from database.db import create_session

from new_model.Enums import RoleName, Gender
from new_model.handbook.category_new import CategoryNew
from new_model.handbook.new_dan import DanNew
from new_model.handbook.role_new import RoleNew
from utils.constants import JUDO_RANKS


def get_session():
    return create_session()
#
# def init_roles():
#     session = get_session()
#
#     existing_role = [role[0] for role in session.query(Role.name).all()]
#
#     roles = []
#     for role in USER_ROLES:
#         new_role = Role(name=role)
#
#         if new_role.name in existing_role:
#             continue
#
#         roles.append(new_role)
#
#     if len(roles) == 0:
#         print(f"Роле уже есть")
#     else:
#         session.add_all(roles)
#         session.commit()
#         session.close()
#
# def init_dans():
#     session = get_session()
#
#     existing_dan = [dan[0] for dan in session.query(Dan.level).all()]
#     dans = []
#     for dan in JUDO_RANKS:
#         desc = JUDO_RANKS[dan]
#         if dan in existing_dan:
#             continue
#
#         new_dan = Dan(level=dan,description=desc)
#         dans.append(new_dan)
#
#     if len(dans) == 0:
#         print(f"Даны уже есть")
#     else:
#         session.add_all(dans)
#         session.commit()
#         session.close()


def init_roles_new():
    session = get_session()

    existing_role = [role[0] for role in session.query(RoleNew.name).all()]

    roles = []
    for role in RoleName:
        new_role = RoleNew(name=role.value, normalized_name=role.value.upper())

        if new_role.name in existing_role:
            continue

        roles.append(new_role)

    if len(roles) == 0:
        print(f"Роле уже есть")
    else:
        session.add_all(roles)
        session.commit()
        session.close()

def init_dans_new():
    session = get_session()

    existing_dan = [dan[0] for dan in session.query(DanNew.level).all()]
    dans = []
    for dan in JUDO_RANKS:
        desc = JUDO_RANKS[dan]
        if dan in existing_dan:
            continue

        new_dan = DanNew(level=dan,description=desc)
        dans.append(new_dan)

    if len(dans) == 0:
        print(f"Даны уже есть")
    else:
        session.add_all(dans)
        session.commit()
        session.close()

def init_category():
    session = get_session()

    categories = [
        # -------- MALE --------
        CategoryNew(name="-23 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=0, max_weight=23, min_year=2014, max_year=2015),
        CategoryNew(name="-26 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=23, max_weight=26, min_year=2014, max_year=2015),
        CategoryNew(name="-30 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=26, max_weight=30, min_year=2014, max_year=2015),
        CategoryNew(name="-34 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=30, max_weight=34, min_year=2014, max_year=2015),
        CategoryNew(name="-38 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=34, max_weight=38, min_year=2014, max_year=2015),
        CategoryNew(name="-42 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=38, max_weight=42, min_year=2014, max_year=2015),
        CategoryNew(name="-46 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=42, max_weight=46, min_year=2014, max_year=2015),
        CategoryNew(name="+46 kg, ПОЛ: мужчины, ГОД: c 2014 по 2015", gender=Gender.male, min_weight=46, max_weight=None, min_year=2014, max_year=2015),

        # -------- FEMALE --------
        CategoryNew(name="-22 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=0, max_weight=22, min_year=2014, max_year=2015),
        CategoryNew(name="-25 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=22, max_weight=25, min_year=2014, max_year=2015),
        CategoryNew(name="-28 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=25, max_weight=28, min_year=2014, max_year=2015),
        CategoryNew(name="-32 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=28, max_weight=32, min_year=2014, max_year=2015),
        CategoryNew(name="-36 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=32, max_weight=36, min_year=2014, max_year=2015),
        CategoryNew(name="-40 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=36, max_weight=40, min_year=2014, max_year=2015),
        CategoryNew(name="-44 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=40, max_weight=44, min_year=2014, max_year=2015),
        CategoryNew(name="+44 kg, ПОЛ: женский, ГОД: c 2014 по 2015", gender=Gender.female, min_weight=44, max_weight=None, min_year=2014, max_year=2015),
    ]

    # Получаем уже существующие категории
    existing = session.query(CategoryNew).all()

    # Делаем set для быстрого поиска
    existing_keys = {
        (c.name, c.gender, c.min_year, c.max_year)
        for c in existing
    }

    categories_new = [
        c for c in categories
        if (c.name, c.gender, c.min_year, c.max_year) not in existing_keys
    ]

    if not categories_new:
        print("Данные уже есть")
    else:
        session.add_all(categories_new)
        session.commit()
        print(f"Добавлено {len(categories_new)} категорий")

    session.close()