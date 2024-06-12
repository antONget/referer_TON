import asyncio

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.types import FSInputFile
from database.requests import get_all_users
from services.get_exel import list_users_to_exel
from config_data.config import Config, load_config
from services.googlesheets import get_list_all_anketa, append_anketa

import logging

router = Router()
config: Config = load_config()


@router.callback_query()
async def all_calback(callback: CallbackQuery) -> None:
    logging.info(f'all_callback: {callback.message.chat.id}')


@router.message()
async def all_message(message: Message) -> None:
    logging.info(f'all_message')
    if message.photo:
        logging.info(f'all_message message.photo')

    if message.sticker:
        logging.info(f'all_message message.sticker')

    list_super_admin = list(map(int, config.tg_bot.admin_ids.split(',')))
    if message.chat.id in list_super_admin:
        logging.info(f'all_message message.admin')
        if message.text == '/get_logfile':
            logging.info(f'all_message message.admin./get_logfile')
            file_path = "py_log.log"
            await message.answer_document(FSInputFile(file_path))

        if message.text == '/get_dbfile':
            logging.info(f'all_message message.admin./get_dbfile')
            file_path = "database.db"
            await message.answer_document(FSInputFile(file_path))

        if message.text == '/get_listusers':
            logging.info(f'all_message message.admin./get_listusers')
            list_user = await get_all_users()
            text = 'Список пользователей:\n'
            for i, user in enumerate(list_user):
                text += f'{i+1}. @{user.username} - {user.ton_balance} TON\n\n'
                if i % 10 == 0 and i > 0:
                    await asyncio.sleep(0.2)
                    await message.answer(text=text)
                    text = ''
            await message.answer(text=text)

        if message.text == '/get_exelusers':
            logging.info(f'all_message message.admin./get_exelusers')
            await list_users_to_exel()
            file_path = "list_user.xlsx"
            await message.answer_document(FSInputFile(file_path))
        if message.text == '/test_googlesheets':
            logging.info(f'all_message message.admin./test_googlesheets')
            id_anketa = len(get_list_all_anketa())
            append_anketa(id_anketa=id_anketa,
                          id_telegram_refer=message.chat.id,
                          username_refer=message.from_user.username,
                          id_telegram_referer=555,
                          username_referer="username_referer",
                          link_post="link_post",
                          status="status")


