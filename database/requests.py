from database.models import User
from database.models import async_session

# Для тестов функций надо раскоментить, а выше закомменть
# from models import User
# from models import async_session


import logging as lg
from dataclasses import dataclass




from sqlalchemy import select  # , update, delete

""" ------------- ADD METHODS -------------"""


async def add_user(data: dict):
    """
    ```
    add user to database:
        data : dict
        {
            'id': int,
            'username': str (without @),
            'referral_link': str,
            'referral_users': str ('123,1234,12345'),
            'ton_balance': int (default=0)
        }
    ```
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == data["id"]))

        if not user:
            session.add(User(**data))
            await session.commit()


async def add_referral_user(main_user_id: int, referral_user_id: int):
    """
    ```
    add referral_user to "referral_users":
        main_user_id : int   (id главного пользователя)
        referral_user_id: int   (id реферала)
    ```
    """
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == main_user_id))
        if user:
            if len(user.referral_users) != 0:
                user.referral_users += f",{referral_user_id}"
                await session.commit()
            else:
                user.referral_users += f"{referral_user_id}"
                await session.commit()


async def increase_ton_balance(tg_id: int, s: float):
    """
    ```
    increase ton_balance:
        tg_id : int
        s : float  (sum of toncoins)
    ```
    """
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            user.ton_balance = format(user.ton_balance + s, '.4f')

            await session.commit()


""" ------------- GET METHODS -------------"""


async def get_balance(tg_id: int):
    """
    ```
    returns:
        ton_balance
    ```
    """
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user.ton_balance
        else:
            return 0


async def get_referral_link(tg_id: int):
    """
    ```
    returns:
        referral_link : str
    ```
    """
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user.referral_link
        else:
            return None


async def _get_username_from_id(tg_id: int):
    '''```code
    returns:
        username for function "get_referral_users"
    ```'''
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == tg_id))
        if user:
            return user.username
        else:
            return None


async def get_referral_users(tg_id: int):
    '''```python
    returns:
        По вашей реферальной ссылке подписались на бот {len(users)} пользователей:\n\n

        1. @username1
        2. @username2
        3. @username3
    ```'''
    async with async_session() as session:
        users = (await session.scalar(select(User).where(User.id == tg_id))).referral_users

        if users:
            users = users.split(",")
            s = f'По вашей реферальной ссылке подписались на бот {len(users)} пользователей:\n\n'
            c = 1
            for user_id in users:
                s += f"{c}. @{await _get_username_from_id(int(user_id))}\n"
                c += 1

            return s
        else:
            return None


async def can_add_ref_user(tg_id) -> bool:
    """
    ```
    returns:
       True if user not in db else False
    ```
    """
    async with async_session() as session:
        users = (await session.scalars(select(User))).all()
        c = 0
        for user in users:
            if user:
                if len(user.referral_users) != 0:
                    ref_users = user.referral_users.split(",")
                    for ref_user in ref_users:
                        if ref_user == str(tg_id):
                            c += 1

        if c != 0:
            return False
        return True


async def get_all_users() -> list[User]:
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users


async def get_user_from_id(user_id: int):
    """
    Получаем информацию из таблицы User по пользователю по его id телеграм
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        return user


async def get_user_ton_addr_by_id(user_id: int):
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == user_id))
        if user:
            return user.crypto_ton_addr
        else:
            return None


'''       UPDATE       '''

@dataclass
class UserStatus:
    passed = "None"
    payed = "PAYED"
    not_payed = "NOT_PAYED"
    on_work = "ON_WORK"


async def update_status(user_id: int, status: UserStatus):
    """
    Обновляем статус пользователя
    """
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == user_id))
        if user:
            user.status = status
            await session.commit()


async def update_user_ton_addr(user_id: int, user_addr: str):
    async with async_session() as session:
        user: User = await session.scalar(select(User).where(User.id == user_id))
        if user:
            user.crypto_ton_addr = user_addr
            await session.commit()

