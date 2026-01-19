from config import USER_ROLES
from database.db import create_session
from models.Dan import Dan
from models.Enums import RoleName
from models.role import Role
from new_model.handbook.new_dan import DanNew
from new_model.handbook.role_new import RoleNew
from utils.constants import JUDO_RANKS


def get_session():
    return create_session()

def init_roles():
    session = get_session()

    existing_role = [role[0] for role in session.query(Role.name).all()]

    roles = []
    for role in USER_ROLES:
        new_role = Role(name=role)

        if new_role.name in existing_role:
            continue

        roles.append(new_role)

    if len(roles) == 0:
        print(f"Роле уже есть")
    else:
        session.add_all(roles)
        session.commit()
        session.close()

def init_dans():
    session = get_session()

    existing_dan = [dan[0] for dan in session.query(Dan.level).all()]
    dans = []
    for dan in JUDO_RANKS:
        desc = JUDO_RANKS[dan]
        if dan in existing_dan:
            continue

        new_dan = Dan(level=dan,description=desc)
        dans.append(new_dan)

    if len(dans) == 0:
        print(f"Даны уже есть")
    else:
        session.add_all(dans)
        session.commit()
        session.close()

def init_roles_new():
    session = get_session()

    existing_role = [role[0] for role in session.query(RoleNew.name).all()]

    roles = []
    for role in RoleName:
        new_role = RoleNew(name=role.name)

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
