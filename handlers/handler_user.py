from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatMemberMember, ChatMemberAdministrator, ChatMemberOwner
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.filters import Filter


from config_data.config import Config, load_config
from database.requests import add_user, get_balance, get_referral_users, get_referral_link
from keyboards.keyboard_user import keyboards_subscription, keyboards_main


import logging
import asyncio


from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
user_dict = {}
config: Config = load_config()


class User(StatesGroup):
    username = State()


class ChannelProtect(Filter):
    async def __call__(self, message: Message):
        u_status = await bot.get_chat_member(chat_id=config.tg_bot.channel_name, user_id=message.from_user.id)
        if isinstance(u_status, ChatMemberMember) or isinstance(u_status, ChatMemberAdministrator) \
                or isinstance(u_status, ChatMemberOwner):
            return True
        if isinstance(message, CallbackQuery):
            await message.answer('')
            await message.message.answer(text=f'Чтобы получать вознаграждения за приглашенных пользователей, а самому'
                                              f' найти вакансию своей мечты подпишись на канал'
                                              f'<a href="{config.tg_bot.channel_name}">{config.tg_bot.channel_name}</a>',
                                         reply_markup=await keyboards_subscription(),
                                         parse_mode='html')
        else:
            await message.answer(text=f'Чтобы получать вознаграждения за приглашенных пользователей, а самому найти'
                                      f' вакансию своей мечты подпишись на канал'
                                      f'<a href="{config.tg_bot.channel_name}">{config.tg_bot.channel_name}</a>',
                                 reply_markup=await keyboards_subscription(),
                                 parse_mode='html')
        return False


@router.message(ChannelProtect(), CommandStart())
async def process_start_command_user(message: Message,  command: CommandObject) -> None:
    logging.info("process_start_command_user")
    referer_id = 0
    args = command.args
    if args:
        referer_id = decode_payload(args)
        print(referer_id)
    link = await create_start_link(bot=bot, payload=str(message.from_user.id), encode=True)
    await add_user({"id": message.from_user.id, "username": message.from_user.username, "referral_link": link})
    await user_subscription(message)


@router.callback_query(ChannelProtect(), F.data == 'subscription')
async def process_press_subscription(callback: CallbackQuery, bot: Bot):
    logging.info(f'process_press_subscription: {callback.message.chat.id}')
    await callback.answer('')
    await user_subscription(message=callback)


async def user_subscription(message: Message | CallbackQuery):
    logging.info(f'user_subscription: {message.from_user.id}')
    if isinstance(message, Message):
        await message.answer(text=f'Привет, {message.from_user.first_name} 👋\n'
                                  f'Бот позволяет ....',
                             reply_markup=await keyboards_main())
    else:
        await message.message.answer(text=f'Привет, {message.from_user.first_name} 👋\n'
                                          f'Бот позволяет ....',
                                     reply_markup=await keyboards_main())


@router.message(F.text == 'Баланс')
async def get_user_balance(message: Message):
    logging.info(f'get_user_balance: {message.from_user.id}')
    balance_user = await get_balance(message.from_user.id)
    await message.answer(text=f'Ваш баланс составляет:\n'
                              f'{balance_user} TON')


@router.message(F.text == 'Пригласить реферала')
async def get_link_ref(message: Message, bot: Bot):
    logging.info(f'get_link_referal: {message.chat.id}')
    link = await get_referral_link(message.from_user.id)
    await message.answer(text=f'Ваша реферальная ссылка:\n'
                              f'{link}')


@router.message(F.text == 'Список рефералов')
async def get_list_referrals(message: Message):
    logging.info(f'get_list_user_referal: {message.chat.id}')

    msg = await get_referral_users(message.from_user.id)

    if len(msg) > 4096:
        for x in range(0, len(msg), 4096):
            await message.answer(msg[x:x+4096])
            await asyncio.sleep(0.2)
    else:
        await message.answer(msg)
