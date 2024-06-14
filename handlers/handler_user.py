from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatMemberMember, ChatMemberAdministrator, ChatMemberOwner
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state


from config_data.config import Config, load_config
from database.requests import add_user, get_balance, get_referral_users, get_referral_link, \
    add_referral_user, _get_username_from_id, get_user_from_id, increase_ton_balance
from keyboards.keyboard_user import keyboards_subscription, keyboards_main, yes_or_no, on_work, confirm
from crypto.CryptoHelper import pay_ton_to, CodeErrorFactory
from services.googlesheets import get_list_all_anketa, append_anketa, update_status_anketa

import logging
import asyncio

router = Router()
user_dict = {}
config: Config = load_config()


class ChannelProtect(Filter):
    async def __call__(self, message: Message, bot: Bot):
        u_status = await bot.get_chat_member(chat_id=load_config().tg_bot.channel_name, user_id=message.from_user.id)
        if isinstance(u_status, ChatMemberMember) or isinstance(u_status, ChatMemberAdministrator) \
                or isinstance(u_status, ChatMemberOwner):
            return True
        if isinstance(message, CallbackQuery):
            await message.answer('')
            await message.message.answer(text=f'Чтобы получать вознаграждения за приглашенных пользователей, а самому'
                                              f' найти вакансию своей мечты подпишись на канал '
                                              f'<a href="{config.tg_bot.channel_name}">'
                                              f'{config.tg_bot.channel_name}</a>',
                                         reply_markup=keyboards_subscription(),
                                         parse_mode='html')
        else:
            await message.answer(text=f'Чтобы получать вознаграждения за приглашенных пользователей, а самому найти'
                                      f' вакансию своей мечты подпишись на канал'
                                      f'<a href="{config.tg_bot.channel_name}">{config.tg_bot.channel_name}</a>',
                                 reply_markup=keyboards_subscription(),
                                 parse_mode='html')
        return False


@router.message(ChannelProtect(), CommandStart())
async def process_start_command_user(message: Message, command: CommandObject, bot: Bot) -> None:
    logging.info("process_start_command_user")
    args = command.args
    if args:
        referrer_id = int(decode_payload(args))
        print(referrer_id)
        if not await get_user_from_id(user_id=message.from_user.id):
            await add_referral_user(main_user_id=referrer_id, referral_user_id=message.from_user.id)
            #
            # try:
            #     tr = await pay_ton_to(referrer_id, 0.15)
            #     if tr.status == 'completed':
            #         await bot.send_message(chat_id=referrer_id,
            #                                text=f'💸 По вашей ссылке перешел @{message.from_user.username},'
            #                                     f' вам было начислено 0.15 TON \n@CryptoBot')
            #     else:
            #         for admin_id in config.tg_bot.admin_ids.split(','):
            #             await bot.send_message(chat_id=admin_id,
            #                                    text=f'❗️Что-то пошло не так, и пользователю'
            #                                         f' {await _get_username_from_id(referrer_id)} не пришло 0.15 TON'
            #                                         f' за приглашенного @{message.from_user.username}')
            #
            # except Exception as e:
            #     logging.error(e)
            #     for admin_id in config.tg_bot.admin_ids.split(','):
            #         await bot.send_message(chat_id=admin_id,
            #                                text=f'❗️Что-то пошло не так, и пользователю'
            #                                     f' {await _get_username_from_id(referrer_id)} не пришло 0.15 TON'
            #                                     f' за приглашенного @{message.from_user.username}')

            link = await create_start_link(bot=bot, payload=str(message.from_user.id), encode=True)
            await add_user({"id": message.from_user.id, "username": message.from_user.username, "referral_link": link,
                            "referer_id": referrer_id})
            await user_subscription(message)
        else:
            user = await get_user_from_id(user_id=message.chat.id)
            if user.referer_id != referrer_id:
                await message.answer('Вас может пригласить только один человек!')
            await user_subscription(message)
    else:
        link = await create_start_link(bot=bot, payload=str(message.from_user.id), encode=True)
        await add_user({"id": message.from_user.id, "username": message.from_user.username, "referral_link": link})
        await user_subscription(message)


@router.callback_query(ChannelProtect(), F.data == 'subscription')
async def process_press_subscription(callback: CallbackQuery):
    logging.info(f'process_press_subscription: {callback.message.chat.id}')
    await callback.answer('')
    await user_subscription(message=callback)


async def user_subscription(message: Message | CallbackQuery):
    logging.info(f'user_subscription: {message.from_user.id}')
    if isinstance(message, Message):
        await message.answer(text=f'Привет, {message.from_user.first_name} 👋\n'
                                  f'Бот позволяет ....',
                             reply_markup=keyboards_main())
    else:
        await message.message.answer(text=f'Привет, {message.from_user.first_name} 👋\n'
                                          f'Бот позволяет ....',
                                     reply_markup=keyboards_main())


@router.message(F.text == 'Баланс')
async def get_user_balance(message: Message):
    logging.info(f'get_user_balance: {message.from_user.id}')
    balance_user = await get_balance(message.from_user.id)
    await message.answer(text=f'Ваш баланс составляет:\n'
                              f'{balance_user} TON')


@router.message(F.text == 'Пригласить реферала')
async def get_link_ref(message: Message):
    logging.info(f'get_link_referal: {message.chat.id}')
    link = await get_referral_link(message.from_user.id)
    await message.answer(text=f'Ваша реферальная ссылка:\n'
                              f'{link}')


@router.message(F.text == 'Список рефералов')
async def get_list_referrals(message: Message):
    logging.info(f'get_list_user_referal: {message.chat.id}')

    msg = await get_referral_users(message.from_user.id)
    if msg:
        print(msg)
        if len(msg) > 4096:
            for x in range(0, len(msg), 4096):
                await message.answer(msg[x:x + 4096])
                await asyncio.sleep(0.2)
        else:
            await message.answer(msg)
    else:
        await message.answer(text='В вашем списке никого нет!')


class UserAnketa(StatesGroup):
    Anketa = State()
    confirm = State()
    id = State()


@router.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    await message.answer('Отмена')
    await state.clear()


@router.message(F.text == 'Заполнить анкету на вакансию')
async def make_anketa(message: Message, state: FSMContext):
    logging.info(f'make_anketa: {message.from_user.id}')
    await state.set_state(UserAnketa.Anketa)
    await message.answer('Пришлите ссылку на пост с вакансией из канала!\n\n/cancel для отмены')


@router.message(UserAnketa.Anketa)
async def get_anketa(message: Message, state: FSMContext):
    logging.info(f'get_anketa: {message.from_user.id}')
    await state.update_data(anketa=message.text)
    await message.answer('Подтверждаете?', reply_markup=yes_or_no())


@router.callback_query(F.data.startswith("linkanketa"))
async def confirm_anketa(callback: CallbackQuery, state: FSMContext, bot: Bot):
    logging.info(f'confirm_anketa: {callback.message.from_user.id}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    answer = callback.data.split('_')[1]
    if answer == 'confirm':
        msg = await callback.message.answer('Отправка анкеты...')
        id_anketa = len(get_list_all_anketa())
        await state.update_data(id_anketa=id_anketa)
        user_dict[callback.message.chat.id] = await state.get_data()
        anketa = user_dict[callback.message.chat.id]['anketa']
        user = await get_user_from_id(user_id=callback.message.chat.id)
        if user.referer_id != 0:
            referer = await get_user_from_id(user_id=user.referer_id)
            id_telegram_referer = user.referer_id
            username_referer = referer.username
        else:
            id_telegram_referer = 0
            username_referer = 'none'
        append_anketa(id_anketa=id_anketa,
                      id_telegram_refer=callback.message.chat.id,
                      username_refer=callback.from_user.username,
                      id_telegram_referer=id_telegram_referer,
                      username_referer=username_referer,
                      link_post=anketa,
                      status="⚠️")
        await asyncio.sleep(3)
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=msg.message_id)
        await callback.answer(text='Отлично, ваша анкета отправлена!',
                              show_alert=True)
        await callback.message.answer(text='Начисление TON произойдет после выхода на работу. \n\n'
                                           'Также вы можете воспользоваться реферальной программой и получать TON за'
                                           ' приглашенных пользователей')
        await callback.message.answer(text='Для оперативного начисления TON после выхода на работу нажми на кнопку'
                                           ' "Хочу TON"',
                                      reply_markup=on_work(id_anketa=id_anketa))
        await state.set_state(default_state)
    else:
        await callback.message.answer(text='Вы отменили отправку анкеты',
                                      reply_markup=keyboards_main())
        await state.set_state(default_state)
    await callback.answer()


async def confirm_complete(bot: Bot, message: Message):
    for admin_id in config.tg_bot.admin_ids.split(','):
        try:
            await bot.send_message(chat_id=int(admin_id),
                                   text=f'Подтвердите начисление пользователю @{message.from_user.username}!',
                                   reply_markup=confirm(message.from_user.id))
        except:
            pass


@router.callback_query(F.data.startswith('wishton_'))
async def want_ton(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer(text='Информация направлена администратору и после подтверждения вам будет начислено'
                               ' вознаграждение. Спасибо!',
                          show_alert=True)
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    user_dict[callback.message.chat.id] = await state.get_data()
    anketa = user_dict[callback.message.chat.id]['anketa']
    id_anketa = user_dict[callback.message.chat.id]['id_anketa']
    # username = callback.from_user.username
    for admin_id in config.tg_bot.admin_ids.split(','):
        try:
            await bot.send_message(chat_id=int(admin_id),
                                   text=f'Пользователь @{callback.from_user.username}, откликнувшийся на вакансию:\n'
                                        f' {anketa},'
                                        f' вышел на работу.\n'
                                        f'Подтвердите это изменение сведения в гугл таблице строка № {id_anketa}')
            await bot.send_message(chat_id=int(admin_id),
                                   text=f'Подтвердите начисление пользователю @{callback.from_user.username}!',
                                   reply_markup=confirm(callback.message.chat.id))
        except:
            pass
    await state.set_state(default_state)
    await callback.answer()


@router.callback_query(F.data.startswith('confirm_pay_'))
async def transfer_pay_to(callback: CallbackQuery, bot: Bot, state: FSMContext):
    logging.info(f'transfer_pay_to: {callback.data.split("_")[-1]}')
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    user_to_pay = int(callback.data.split('_')[-1])
    update_status_anketa(status='✅', telegram_id=user_to_pay)
    try:
        tr = await pay_ton_to(user_to_pay, 0.15)
        await increase_ton_balance(tg_id=user_to_pay, s=0.15)
        if tr.status == 'completed':
            await callback.message.answer(
                f'✅ Пользователю @{await _get_username_from_id(user_to_pay)} отправлено <strong>0.15 TON</strong>',
                parse_mode='html')
            try:
                await bot.send_message(chat_id=user_to_pay,
                                       text='Вам было отправлено 0.15 TON\n\n'
                                            'Проверьте ваш кошелек @CryptoBot')
            except:
                pass
            update_status_anketa(status='💰', telegram_id=user_to_pay)
        else:
            for admin_id in config.tg_bot.admin_ids.split(','):
                try:
                    await bot.send_message(chat_id=int(admin_id),
                                           text=f'❗️Что-то пошло не так, и пользователю'
                                                f' {await _get_username_from_id(user_to_pay)} не пришло 0.15 TON,'
                                                f' проверьте кошелек, скорее всего там недостаточно средств!')
                except:
                    pass

    except Exception as e:
        err = CodeErrorFactory(400)
        # logging.info([err.args, e.args])
        if e.args[0] == err.args[0]:
            for admin_id in config.tg_bot.admin_ids.split(','):
                try:
                    await bot.send_message(chat_id=int(admin_id),
                                           text=f'❗️Недостаточно средств! Пользователю'
                                                f' @{await _get_username_from_id(user_to_pay)} не пришло 0.15 TON'
                                                f' за приглашенного реферала')
                except:
                    pass
    await callback.answer()


@router.callback_query(F.data.startswith('cancel_pay_'))
async def cancel_pay(callback: CallbackQuery, bot: Bot, state: FSMContext):
    logging.info(f'cancel_pay: {callback.data.split("_")[-1]}')
    await callback.answer('')
    user_to_pay = int(callback.data.split('_')[-1])
    await callback.message.answer(text=f'❌ Пользователю @{await _get_username_from_id(user_to_pay)} оплата'
                                       f' не отправлена',
                                  parse_mode='html')
    try:
        await bot.send_message(chat_id=user_to_pay,
                               text='Оплата была не одобрена администрацией')
    except:
        pass
    update_status_anketa(status='❌', telegram_id=user_to_pay)
    await callback.answer()