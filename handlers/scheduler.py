from services.googlesheets import get_list_all_anketa, get_list_anketa, update_status_anketa
from keyboards.keybord_scheduler import keyboards_confirm_pay

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery
from config_data.config import Config, load_config
from database.requests import get_user_from_id, UserStatus
import requests
from datetime import datetime, date, timedelta
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
    # 1-id_anketa, 2-id_telegram_referal, 3-username_referal, 4-id_telegram_referer, 5-username_referer,
    # 6-name, 7-phone,	8-city, 9-email, 10-link_post,
    # 11-vacancy, 12-status, 13-date_anketa, 14-date_work
    first_row = list_anketa[0]
    anketa = {}
    # !!!! days требуется выставить по количеству дней после начала работы
    date_today = datetime.now() - timedelta(days=30)
    date_today_str = date_today.strftime('%d/%m/%Y')
    # если список не пустой, то пропускаем '💰'
    if list_anketa:
        for item in list_anketa:
            # если нашли прерываем цикл и обрабатываем событие
            if item[first_row.index("status")] != '💰':
                # получаем дату текущую
                list_date_today = date_today_str.split('/')
                date_today = date(int(list_date_today[2]), int(list_date_today[1]), int(list_date_today[0]))
                # получаем дату заполнения анкеты
                if item[first_row.index("date_work")] not in ['', "date_work"]:
                    list_date_work = item[first_row.index("date_work")].split('/')
                else:
                    continue
                date_work = date(int(list_date_work[2]), int(list_date_work[1]), int(list_date_work[0]))
                # если прошел месяц (30 дней)
                if date_today >= date_work:
                    # получаем информацию о пользователе
                    user = await get_user_from_id(user_id=int(item[first_row.index("id_telegram_referal")]))
                    # проверяем его статус в БД
                    if user.status != UserStatus.payed:
                        # получаем информацию о его анкете
                        for i, value in enumerate(item):
                            anketa[list_anketa[0][i]] = value
                        break
        # если событий целевого действия нет, то информируем админа
        else:
            # получаем список админов
            list_super_admin = config.tg_bot.admin_ids.split(',')
            # отправляем всем админам информационное сообщение
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
        # обработка целевого действия совершенного пользователем, получаем подтверждение от админа о
        # начислении вознаграждения
        # получаем список администраторов
        list_super_admin = config.tg_bot.admin_ids.split(',')
        # отправляем всем администраторам сообщение
        for id_superadmin in list_super_admin:
            result = get_telegram_user(user_id=int(id_superadmin),
                                       bot_token=config.tg_bot.token)
            if 'result' in result:
                try:
                    await bot.send_message(chat_id=int(id_superadmin),
                                           text=f'Подтвердите начисление пользователю {anketa["username_referal"]}',
                                           reply_markup=keyboards_confirm_pay(id_anketa=anketa['id_anketa']))
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

