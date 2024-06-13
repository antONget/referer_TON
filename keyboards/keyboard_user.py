from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import logging


def keyboards_subscription():
    logging.info(f'keyboards_subscription')
    button_1 = InlineKeyboardButton(text='Я подписался', callback_data='subscription')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1]], )
    return keyboard


def keyboards_main() -> ReplyKeyboardMarkup:
    logging.info("keyboards_main")
    button_1 = KeyboardButton(text='Заполнить анкету на вакансию')
    button_2 = KeyboardButton(text='Пригласить реферала')
    button_3 = KeyboardButton(text='Баланс')
    button_4 = KeyboardButton(text='Список рефералов')
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[button_1], [button_2], [button_3], [button_4]],
        resize_keyboard=True
    )
    return keyboard


def yes_or_no() -> ReplyKeyboardMarkup:
    logging.info("keyboards_main")
    button_1 = InlineKeyboardButton(text='Да', callback_data='linkanketa_confirm')
    button_2 = InlineKeyboardButton(text='Нет', callback_data='linkanketa_cancel')

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_1, button_2]]
    )
    return keyboard


def on_work(id_anketa: int) -> ReplyKeyboardMarkup:
    logging.info("on_work")
    button_1 = InlineKeyboardButton(text='Хочу TON', callback_data=f'wishton_{id_anketa}')
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_1]]
    )
    return keyboard


def confirm(user_id: int) -> ReplyKeyboardMarkup:
    logging.info("confirm_pay")
    button_1 = InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_pay_{user_id}')
    button_2 = InlineKeyboardButton(text='Отмена', callback_data=f'cancel_pay_{user_id}')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2]], )
    return keyboard



