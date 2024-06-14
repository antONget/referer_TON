from aiogram.types import CallbackQuery
from aiogram import Bot, Router, F

import logging
from services.googlesheets import get_list_anketa, update_status_anketa
from handlers.scheduler import send_ton
from crypto.CryptoHelper import pay_ton_to
from database.requests import increase_ton_balance

router = Router()


@router.callback_query(F.data.startswith('schcancel_pay_'))
async def process_cancel_pay(callback: CallbackQuery, bot: Bot):
    """
    Отмена начисления вознаграждения, изменяем статус анкеты и запускаем поиск нового события
    """
    logging.info(f'process_cancel_pay: {callback.message.chat.id}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    id_anketa = int(callback.data.split('_')[2])
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    await callback.answer(text=f'Начисление для пользователя @{info_anketa[2]} отменено', show_alert=True)
    update_status_anketa(status='❌', telegram_id=int(info_anketa[1]))
    await bot.send_message(chat_id=int(info_anketa[1]),
                           text='Оплата была не одобрена администрацией')
    await callback.answer()
    await send_ton(bot=bot)


@router.callback_query(F.data.startswith('schconfirm_pay_'))
async def process_cancel_pay(callback: CallbackQuery, bot: Bot):
    """
    Подтверждение начисления вознаграждения пользователю и его рефереру, запуск поиска нового события
    """
    logging.info(f'process_cancel_pay: {callback.message.chat.id}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    id_anketa = int(callback.data.split('_')[2])
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    await callback.answer(text=f'Начисление для пользователя @{info_anketa[2]} подтверждено', show_alert=True)
    await pay_ton_to(user_id=int(info_anketa[1]), amount=0.17)
    await increase_ton_balance(tg_id=int(info_anketa[1]), s=0.17)
    update_status_anketa(status='💰', telegram_id=int(info_anketa[1]))
    await bot.send_message(chat_id=int(info_anketa[1]),
                           text='Вам было отправлено 0.15 TON\n\n'
                                'Проверьте ваш кошелек @CryptoBot')
    if int(info_anketa[3]):
        print(info_anketa)
        await pay_ton_to(user_id=int(info_anketa[3]), amount=0.15)
        await increase_ton_balance(tg_id=int(info_anketa[3]), s=0.15)
    await callback.answer()
    await send_ton(bot=bot)
