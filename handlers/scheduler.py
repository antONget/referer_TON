from services.googlesheets import get_list_all_anketa, get_list_anketa, update_status_anketa
from keyboards.keybord_scheduler import keyboards_confirm_pay

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery
from config_data.config import Config, load_config
from database.requests import get_user_from_id, UserStatus
import requests
import logging
config: Config = load_config()
router = Router()


def get_telegram_user(user_id, bot_token):
    """
    Проверка возможности отправки сообщения, на случай если пользователь заблокировал бота
    :param user_id:
    :param bot_token:
    :return:
    """
    url = f'https://api.telegram.org/bot{bot_token}/getChat'
    data = {'chat_id': user_id}
    response = requests.post(url, data=data)
    return response.json()


async def send_ton(bot: Bot):
    """
    Функция проверяет выполнение целевого действия для начисления вознаграждения
    """
    # получаем список заполнивших анкету
    list_anketa = get_list_all_anketa()
    anketa = 0
    # если список не пустой, то ищем статус анкеты '✅'
    if list_anketa:
        for item in list_anketa:
            # если нашли прерываем цикл и обрабатываем событие
            if item[9] == '✅':
                user = await get_user_from_id(user_id=int(item[1]))
                if user.status != UserStatus.payed:
                    anketa = item
                    break
        # если событий целевого действия нет, то информируем админа
        else:
            list_super_admin = config.tg_bot.admin_ids.split(',')
            for id_superadmin in list_super_admin:
                result = get_telegram_user(user_id=int(id_superadmin),
                                           bot_token=config.tg_bot.token)
                if 'result' in result:
                    try:
                        await bot.send_message(chat_id=int(id_superadmin),
                                               text=f'Нет новых пользователей заполнивших анкету на вакансию и'
                                                    f' совершивших целевое действие для начисления вознаграждения!')
                    except:
                        pass
        # обработка целевого действия совершенного пользователем, получаем подтверждение от админа о начислении вознаграждения
        list_super_admin = config.tg_bot.admin_ids.split(',')
        for id_superadmin in list_super_admin:
            result = get_telegram_user(user_id=int(id_superadmin),
                                       bot_token=config.tg_bot.token)
            if 'result' in result:
                try:
                    await bot.send_message(chat_id=int(id_superadmin),
                                           text=f'Подтвердите начисление пользователю {anketa[2]}',
                                           reply_markup=keyboards_confirm_pay(id_anketa=anketa[0]))
                except:
                    pass
    # если список пустой, то информируем админа
    else:
        list_super_admin = config.tg_bot.admin_ids.split(',')
        for id_superadmin in list_super_admin:
            result = get_telegram_user(user_id=int(id_superadmin),
                                       bot_token=config.tg_bot.token)
            if 'result' in result:
                try:
                    await bot.send_message(chat_id=int(id_superadmin),
                                           text=f'Нет пользователей выполнивших целевое действие для начисления'
                                                f' вознаграждения')
                except:
                    pass

