from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.deep_linking import create_start_link, decode_payload

from config_data.config import Config, load_config
from module.data_base import create_table_users, add_user, get_balance_user, get_list_user_referal
from keyboards.keyboard_user import keyboards_subscription, keyboards_main


import logging


from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
user_dict = {}
config: Config = load_config()


class User(StatesGroup):
    username = State()


@router.message(Command('ref'))
async def mt_referal_menu (message: Message, bot: Bot):
    link = await create_start_link(bot, str(message.from_user.id), encode=True)
    await message.answer(text=f'{link}')


@router.message(CommandStart())
async def process_start_command_user(message: Message, bot: Bot, command: Command) -> None:
    logging.info("process_start_command_user")
    create_table_users()
    referer_id = 0
    if len(message.text.split()) == 2:
        args = command.args
        referer_id = decode_payload(args)
        print(referer_id)
    add_user(telegram_id=message.chat.id,
             username=message.from_user.username,
             referer_id=referer_id)
    user_channel_status = await bot.get_chat_member(chat_id=config.tg_bot.channel_name,
                                                    user_id=message.from_user.id)
    if user_channel_status.status != 'left':
        await user_subscription(message=message)
    else:
        await message.answer(text=f'Чтобы получать вознаграждения за приглашенных пользователей, а самому найти'
                                  f' вакансию своей мечты подпишись на канал'
                                  f'<a href="{config.tg_bot.channel_name}">{config.tg_bot.channel_name}</a>',
                             reply_markup=keyboards_subscription(),
                             parse_mode='html')


@router.callback_query(F.data == 'subscription')
async def process_press_subscription(callback: CallbackQuery, bot: Bot):
    logging.info(f'process_press_subscription: {callback.message.chat.id}')
    user_channel_status = await bot.get_chat_member(chat_id=config.tg_bot.channel_name,
                                                    user_id=callback.message.chat.id)
    print(user_channel_status)
    if user_channel_status.status != 'left':
        await user_subscription(message=callback.message)
    else:
        await callback.message.answer(text=f'Просим тебя подписаться на канал: '
                                           f'<a href="{config.tg_bot.channel_name}">{config.tg_bot.channel_name}</a>',
                                      reply_markup=keyboards_subscription(),
                                      parse_mode='html')


async def user_subscription(message: Message):
    logging.info(f'user_subscription: {message.chat.id}')
    await message.answer(text=f'Привет, {message.from_user.first_name} 👋\n'
                              f'Бот позволяет ....',
                         reply_markup=keyboards_main())


@router.message(F.text == 'Баланс')
async def get_user_balance(message: Message):
    logging.info(f'get_user_balance: {message.chat.id}')
    balance_user = get_balance_user(telegram_id=message.chat.id)
    await message.answer(text=f'Ваш баланс составляет:\n'
                              f'{balance_user} TON')


@router.message(F.text == 'Пригласить реферала')
async def get_link_referal(message: Message, bot: Bot):
    logging.info(f'get_link_referal: {message.chat.id}')
    link = await create_start_link(bot, str(message.from_user.id), encode=True)
    await message.answer(text=f'Ваша реферальная ссылка:\n'
                              f'{link}')


@router.message(F.text == 'Список рефералов')
async def get_list_user_referal(message: Message):
    logging.info(f'get_list_user_referal: {message.chat.id}')
    list_user_referal = get_list_user_referal(telegram_id=message.chat.id)
    text = f'По вашей реферальной ссылке подписались на бот {len(list_user_referal)} пользователей:'
    i = 0
    for referal in list_user_referal:
        i += 1
        text += f'{i}. {[referal[2]]}'
        if i % 10 == 0:
            await message.answer(text=text)
            text = ''
    if i % 10:
        await message.answer(text=text)
