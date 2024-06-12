import sqlite3
from config_data.config import Config, load_config
import logging


config: Config = load_config()
db = sqlite3.connect('database.db', check_same_thread=False, isolation_level='EXCLUSIVE')


# СОЗДАНИЕ ТАБЛИЦ - users
def create_table_users() -> None:
    """
    Создание таблицы верифицированных пользователей
    :return: None
    """
    logging.info("table_users")
    with db:
        sql = db.cursor()
        sql.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER,
            username TEXT DEFAULT 'none',
            referer_id INTEGER DEFAULT 0,
            balance INTEGER DEFAULT 0
        )""")
        db.commit()


def add_user(telegram_id: int, username: str, referer_id: int = 0) -> None:
    logging.info(f'add_user')
    with db:
        sql = db.cursor()
        sql.execute('SELECT telegram_id FROM users')
        list_user = [row[0] for row in sql.fetchall()]
        if int(telegram_id) not in list_user:
            sql.execute(f'INSERT INTO users (telegram_id, username, referer_id) '
                        f'VALUES ({telegram_id}, "{username}", {referer_id})')
            db.commit()


def get_list_user() -> list:
    logging.info(f'get_list_user')
    with db:
        sql = db.cursor()
        sql.execute('SELECT * FROM users')
        list_users = [row for row in sql.fetchall()]
        return list_users


def get_balance_user(telegram_id: int) -> int:
    logging.info(f'get_balance_user')
    with db:
        sql = db.cursor()
        sql.execute('SELECT balance FROM users WHERE telegram_id = ?', (telegram_id,))
        return sql.fetchone()[0]


def get_list_user_referal(telegram_id: int) -> list:
    logging.info(f'get_list_user_referal')
    with db:
        sql = db.cursor()
        sql.execute('SELECT * FROM users WHERE referer_id = ?', (telegram_id,))
        list_referal = [row for row in sql.fetchall()]
        return list_referal
