from aiogram.types import CallbackQuery, LinkPreviewOptions
from aiogram import Bot, Router, F

import logging
from services.googlesheets import get_list_anketa, update_status_anketa
from handlers.scheduler import send_ton
from TonCrypto.contract.CryptoHelper import TonWallet, get_ton_in_rub
from database.requests import increase_ton_balance, update_status, UserStatus, _get_username_from_id,\
    update_user_ton_addr, get_user_ton_addr_by_id, get_user_from_id

router = Router()


@router.callback_query(F.data.startswith('schcancel_pay_'))
async def process_cancel_pay(callback: CallbackQuery, bot: Bot):
    """
    Отмена начисления вознаграждения, изменяем статус анкеты и запускаем поиск нового события
    """
    logging.info(f'process_cancel_pay: {callback.message.chat.id}-{callback.data}')
    # удаляем сообщение, которое вызвало апдейт
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    # получаем информацию об анкете
    id_anketa = int(callback.data.split('_')[2])
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    await callback.answer(text=f'Начисление для пользователя @{info_anketa[2]} отменено', show_alert=True)
    # обновляем статус в гугл-таблице
    update_status_anketa(status='❌', telegram_id=int(info_anketa[1]))
    try:
        # информируем пользователя
        await bot.send_message(chat_id=int(info_anketa[1]),
                               text='Оплата была не одобрена администрацией')
    except:
        pass
    await callback.answer()
    # запускаем функцию получения нового подтверждения для пользователя
    await send_ton(bot=bot)


@router.callback_query(F.data.startswith('schconfirm_pay_'))
async def process_cancel_pay(callback: CallbackQuery, bot: Bot):
    """
    Подтверждение начисления вознаграждения пользователю и его рефереру, запуск поиска нового события
    """
    logging.info(f'process_cancel_pay: {callback.message.chat.id}-{callback.data}')
    # удаляем сообщение, которое вызвало апдейт
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    # получаем информацию об анкете
    id_anketa = int(callback.data.split('_')[2])
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    # получаем информацию о пользователе
    user = await get_user_from_id(int(info_anketa[1]))
    # если пользователь еще не получал вознаграждения по этой анкете
    if user.status != UserStatus.payed:
        # информируем администратора
        await callback.answer(text=f'Начисление для пользователя @{info_anketa[2]} подтверждено', show_alert=True)
        # получаем id телеграм пользователя
        user_id = info_anketa[1]
        # адрес кошелька
        user_addr = await get_user_ton_addr_by_id(user_id)
        # формируем строку вакансии
        vacancy = ''
        amount = 0
        logging.info(f'info_anketa: {info_anketa}')
        if info_anketa[10] == 'merchandiser':
            amount = 2000
        elif info_anketa[10] == 'mysteryShopper':
            amount = 1000
        elif info_anketa[10] == 'consultant':
            amount = 5000
        # !!! получаем количество TON по курсу
        amount_ton = await get_ton_in_rub(amount=amount) / 1000
        logging.info(f'amount_ton: {amount_ton}')
        # пользователю начисляем 50% от суммы
        # amount_user_ton = round(amount_ton / 2, 2)
        # производим начисление вознаграждения
        # tr = await TonWallet.transfer(amount=amount_user_ton, to_addr=user_addr)
        # если платеж прошел
        # if tr == 'ok':
            # увеличиваем баланс пользователя
            # await increase_ton_balance(tg_id=int(info_anketa[1]), s=amount_user_ton)
        # изменяем статус анкеты в гугл-таблице
        update_status_anketa(status='💰', telegram_id=int(info_anketa[1]))
        # изменяем статус пользователя в БД
        await update_status(int(info_anketa[1]), UserStatus.payed)

            # try:
            #     # отправляем пользователя сообщение
            #     await bot.send_message(chat_id=int(info_anketa[1]),
            #                            text=f'Вам было отправлено {amount_user_ton} TON\n\n'
            #                                 f'Проверьте ваш <a href="https://tonscan.org/address/{user_addr}">'
            #                                 f'кошелек.</a>',
            #                            parse_mode='html',
            #                            link_preview_options=LinkPreviewOptions(is_disabled=True))
            # except:
            #     pass
        # если у пользователя есть реферал
        if int(info_anketa[3]):
            # производим начисление вознаграждения
            tr = await TonWallet.transfer(amount={amount_ton}, to_addr=user_addr)
            # если платеж прошел успешно
            if tr == 'ok':
                # увеличиваем баланс
                await increase_ton_balance(tg_id=int(info_anketa[3]), s=amount_ton)
                try:
                    # информируем реферера
                    await bot.send_message(chat_id=int(info_anketa[3]),
                                           text=f'Вам отправлено <strong>{amount_ton} TON '
                                                f'</strong>за приглашенного пользователя'
                                                f' @{await _get_username_from_id(int(info_anketa[1]))}',
                                           parse_mode='html')
                except:
                    pass
    else:
        await callback.answer(text='Этот пользователь уже получил вознаграждение!',
                              show_alert=True)
    await callback.answer()
    await send_ton(bot=bot)
