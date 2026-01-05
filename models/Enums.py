from enum import Enum


class Gender(Enum):
    male = 0,
    female = 1


def translate_gender(gender):
    return Gender.male if gender == 'мужской' else Gender.female