Подключение к базе данных PostgreSQL с использованием Python и библиотеки psycopg2
===============================================================

### Необходимые библиотеки

Надо скачать пакеты необходимые для работы API. Для этого используйте pip:

```bash
  pip install -r requirements.txt
```
Если вы добавляете и обновлаете зависимости, не забудьте обновить файл requirements.txt:

```bash
  pip freeze > requirements.txt
```
### Пример подключения к базе данных PostgreSQL

Для изменения подключения к базе данных PostgreSQL, отредактируйте параметры в файле `app.py`, следующем примере кода:

```python

from flask import Flask

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://{user}:{пароль}@localhost:5432/judo_tournament?client_encoding=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
```

Замените `{user}` и `{пароль}` на ваши реальные учетные данные для подключения к базе данных PostgreSQL.

Также его надо заменить в файле `db.py`, который находится в папке `database`:

```python
DATABASE_URI = 'postgresql+psycopg2://postgres:password@localhost:5434/judo_tournament'

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
```

### Запуск приложения
После настройки подключения к базе данных, вы можете запустить приложение с помощью следующей команды:

```bash
  py app.py
```

также убедитесь, что Docker c PostgreSQL сервер запущен и база данных доступна.

### Примечание
Если перестали пользоватся то тогда в консоли выполните команду:

```bash
  docker compose down -v
```

Это остановит и удалит контейнеры Docker, а также связанные с ними тома данных. Использовать только для теста или дэбага.