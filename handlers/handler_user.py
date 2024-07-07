from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatMemberMember, ChatMemberAdministrator, ChatMemberOwner,\
    LinkPreviewOptions, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command, CommandObject, or_f
from aiogram.utils.deep_linking import create_start_link, decode_payload
from aiogram.filters import Filter, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state


from config_data.config import Config, load_config
from database.requests import add_user, get_balance, get_referral_users, get_referral_link, \
    add_referral_user, _get_username_from_id, get_user_from_id, increase_ton_balance, update_status, UserStatus,\
    get_user_ton_addr_by_id, update_user_ton_addr
from keyboards.keyboard_user import keyboards_subscription, keyboards_main, yes_or_no, on_work, confirm, yes_or_no_addr,\
    pass_the_state, keyboards_get_contact, keyboard_confirm_phone, keyboard_cancel, keyboard_vacancy, \
    keyboard_confirm_cantact_date

from TonCrypto.contract.CryptoHelper import TonWallet, check_valid_addr, get_ton_in_rub

from services.googlesheets import get_list_all_anketa, append_anketa, update_status_anketa, get_list_anketa, \
    get_info_user
from datetime import datetime
import logging
import asyncio
import re

router = Router()
user_dict = {}
config: Config = load_config()


def validate_russian_phone_number(phone_number):
    # Паттерн для российских номеров телефона
    # Российские номера могут начинаться с +7, 8, или без кода страны
    pattern = re.compile(r'^(\+7|8|7)?(\d{10})$')

    # Проверка соответствия паттерну
    match = pattern.match(phone_number)

    return bool(match)


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
                                      f' вакансию своей мечты подпишись на канал '
                                      f'<a href="{config.tg_bot.channel_name}">{config.tg_bot.channel_name}</a>',
                                 reply_markup=keyboards_subscription(),
                                 parse_mode='html')
        return False


@router.message(ChannelProtect(), CommandStart())
async def process_start_command_user(message: Message, command: CommandObject, bot: Bot, state: FSMContext) -> None:
    """
    Запуск бота пользователем (ввод команды /start) и проверка подписки на канал
    """
    logging.info("process_start_command_user")
    await state.set_state(default_state)
    args = command.args
    if args:
        referrer_id = int(decode_payload(args))

        if not await get_user_from_id(user_id=message.from_user.id):
            await add_referral_user(main_user_id=referrer_id, referral_user_id=message.from_user.id)

            link = await create_start_link(bot=bot, payload=str(message.from_user.id), encode=True)
            if message.from_user.username:
                await add_user(
                    {"id": message.from_user.id, "username": message.from_user.username, "referral_link": link,
                     "referer_id": referrer_id})
            else:
                await add_user(
                    {"id": message.from_user.id, "username": f"None-{message.from_user.id}", "referral_link": link,
                     "referer_id": referrer_id})
            await user_subscription(message)
        else:
            user = await get_user_from_id(user_id=message.chat.id)
            if user.referer_id != referrer_id:
                await message.answer('Вас может пригласить только один человек!')
            await user_subscription(message)
    else:
        link = await create_start_link(bot=bot, payload=str(message.from_user.id), encode=True)
        if message.from_user.username:
            await add_user({"id": message.from_user.id, "username": message.from_user.username, "referral_link": link,
                            "status": 'None'})
        else:
            await add_user({"id": message.from_user.id, "username": f"None-{message.from_user.id}",
                            "referral_link": link, "status": 'None'})
        await user_subscription(message)


@router.callback_query(ChannelProtect(), F.data == 'subscription')
async def process_press_subscription(callback: CallbackQuery, bot: Bot):
    """
    Пользователь нажал кнопку, что он подписался, проверка подписки
    """
    logging.info(f'process_press_subscription: {callback.message.chat.id}')
    link = await create_start_link(bot=bot, payload=str(callback.from_user.id), encode=True)
    if callback.from_user.username:
        await add_user(
            {"id": callback.from_user.id, "username": callback.from_user.username, "referral_link": link})
    else:
        await add_user(
            {"id": callback.from_user.id, "username": f"None-{callback.from_user.id}", "referral_link": link})
    await callback.answer('')
    await user_subscription(message=callback)


async def user_subscription(message: Message | CallbackQuery):
    """
    Меню для подписавшихся пользователей
    """
    logging.info(f'user_subscription: {message.from_user.id}')
    if isinstance(message, Message):
        await message.answer_photo(
            photo='AgACAgIAAxkBAAIG2mZ0W586nnqgd8vmaszoV-6YWiMzAAKj2zEbeLygS5B-4alYFVH_AQADAgADeAADNQQ',
            caption=f'Привет! 👋\n'
                    f'Это бот реферальной системы.\n\n'
                    f'Тут вы сможете:\n'
                    f'✅заполнить анкету на вакансию;\n'
                    f'✅скопировать свою реферальную ссылку и пригласить по ней друга;\n'
                    f'✅узнать свой баланс;\n'
                    f'✅посмотреть список приглашенных людей.',
            reply_markup=keyboards_main()
        )
    else:
        await message.answer_photo(
            photo='AgACAgIAAxkBAAIG2mZ0W586nnqgd8vmaszoV-6YWiMzAAKj2zEbeLygS5B-4alYFVH_AQADAgADeAADNQQ',
            caption=f'Привет! 👋\n'
                    f'Это бот реферальной системы.\n\n'
                    f'Тут вы сможете:\n'
                    f'✅заполнить анкету на вакансию;\n'
                    f'✅скопировать свою реферальную ссылку и пригласить по ней друга;\n'
                    f'✅узнать свой баланс;\n'
                    f'✅посмотреть список приглашенных людей.',
            reply_markup=keyboards_main()
        )


@router.message(F.text == 'Баланс')
async def get_user_balance(message: Message):
    """
    Вывод баланса
    """
    logging.info(f'get_user_balance: {message.from_user.id}')
    balance_user = await get_balance(message.from_user.id)
    await message.answer(text=f'Ваш баланс составляет:\n'
                              f'{balance_user} TON')


@router.message(F.text == 'Пригласить реферала')
async def get_link_ref(message: Message):
    """
    Вывод реферальной ссылки для приглашения пользователей
    """
    logging.info(f'get_link_referal: {message.chat.id}')
    link = await get_referral_link(message.from_user.id)
    await message.answer(text=f'Ваша реферальная ссылка:\n'
                              f'{link}')


@router.message(F.text == 'Список рефералов')
async def get_list_referrals(message: Message):
    """
    Список рефералов
    """
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
    username = State()
    phone = State()
    city = State()
    email = State()
    address = State()
    confirm_addr = State()
    confirm = State()
    id = State()


@router.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    """
    Отмена действия
    """
    await message.answer(text='Действие отменено.',
                         reply_markup=keyboards_main())
    await state.clear()


@router.callback_query(F.data == '/cancel')
async def cancel_cq(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Отмена действия
    """
    logging.info(f'cancel_cq: {callback.message.from_user.id}')
    await callback.message.answer(text='Действие отменено.',
                                  reply_markup=keyboards_main())
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    await state.clear()


@router.message(F.text == 'Заполнить анкету на вакансию')
async def make_anketa(message: Message, state: FSMContext):
    """Нажата кнопка 'Заполнить анкету на вакансию' """
    logging.info(f'make_anketa: {message.from_user.id}')
    # !!! ЗДЕСЬ СЛЕДУЕТ ДОБАВИТЬ ПОДТВЕРЖДЕНИЕ НА РАНЕЕ ВВЕДЕННЫЕ ДАННЫЕ (ИМЯ, НОМЕР ТЕЛЕФОНА, ГОРОД, EMAIL, АДРЕС КОШЕЛЬКА)
    if get_info_user(id_telegram=message.chat.id):
        dict_info_user = get_info_user(id_telegram=message.chat.id)
        address_wallet = await get_user_ton_addr_by_id(user_id=message.chat.id)
        if address_wallet == None:
            wallet = 'отсутствуют данные кошелька'
        else:
            wallet = address_wallet
        await message.answer(text=f'Рад вас приветствовать {dict_info_user["name"]}\n'
                                  f'<i>Номер телефона:</i> {dict_info_user["phone"]}\n'
                                  f'<i>Город:</i> {dict_info_user["city"]}\n'
                                  f'<i>Email:</i> {dict_info_user["email"]}\n'
                                  f'<i>Адрес кошелька:</i> {wallet}\n\n'
                                  f'Проверьте данные и если они верны нажмите "Верно",'
                                  f' иначе "Изменить"',
                             reply_markup=keyboard_confirm_cantact_date(),
                             parse_mode='html')
    else:
        await message.answer(text='Как вас зовут?')
        await state.set_state(UserAnketa.username)


@router.callback_query(F.data.startswith('data_'))
async def confirm_change_data(callback: CallbackQuery, state: FSMContext):
    """
    Подтверждение ранее введенных данных
    """
    logging.info(f'confirm_change_data: {callback.message.from_user.id}')
    answer = callback.data.split('_')[1]
    if answer == 'confirm':
        dict_info_user = get_info_user(id_telegram=callback.message.chat.id)
        await state.update_data(name=dict_info_user['name'])
        await state.update_data(phone=dict_info_user['phone'])
        await state.update_data(city=dict_info_user['city'])
        await state.update_data(email=dict_info_user['email'])
        await callback.message.answer('Пришлите ссылку на пост с вакансией из канала @shoptalkrn',
                                      reply_markup=keyboard_cancel())
        await state.set_state(UserAnketa.Anketa)
    elif answer == 'change':
        await callback.message.edit_text(text='Как вас зовут?',
                                         reply_markup=None)
        await state.set_state(UserAnketa.username)


@router.message(F.text, UserAnketa.username)
async def anketa_get_username(message: Message, state: FSMContext):
    """Получаем имя пользователя. Запрашиваем номер телефона"""
    logging.info(f'anketa_get_username: {message.from_user.id}')
    name = message.text
    await state.update_data(name=name)
    await message.answer(text=f'Рад вас приветствовать {name}. Поделитесь вашим номером телефона ☎️',
                         reply_markup=keyboards_get_contact())
    await state.set_state(UserAnketa.phone)


@router.message(or_f(F.text, F.contact), StateFilter(UserAnketa.phone))
async def process_validate_russian_phone_number(message: Message, state: FSMContext) -> None:
    """Получаем номер телефона пользователя (проводим его валидацию). Подтверждаем введенные данные"""
    logging.info("process_start_command_user")
    if message.contact:
        phone = str(message.contact.phone_number)
    else:
        phone = message.text
        if not validate_russian_phone_number(phone):
            await message.answer(text="Неверный формат номера. Повторите ввод, например 89991112222:")
            return
    await state.update_data(phone=phone)
    await state.set_state(default_state)
    await message.answer(text=f'Записываю, {phone}. Верно?',
                         reply_markup=keyboard_confirm_phone())


@router.callback_query(F.data == 'getphone_back')
async def process_getphone_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Изменение введенного номера телефона"""
    logging.info(f'process_getphone_back: {callback.message.chat.id}')
    await callback.message.answer(text=f'Поделитесь вашим номером телефона ☎️',
                                  reply_markup=keyboards_get_contact())
    await state.set_state(UserAnketa.phone)


@router.callback_query(F.data == 'confirm_phone')
async def process_confirm_phone(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    """Введенный номер телефона подтвержден. Запрос города"""
    logging.info(f'process_confirm_phone: {callback.message.chat.id}')
    await callback.message.answer(text=f'Из какого вы города?',
                                  reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserAnketa.city)


@router.message(F.text, StateFilter(UserAnketa.city))
async def get_city(message: Message, state: FSMContext):
    """Получаем название города. Запрос на отправку номера электронной почты"""
    logging.info(f'get_city: {message.chat.id}')
    await state.update_data(city=message.text)
    await message.answer(text=f'Пришлите адрес эл. почты')
    await state.set_state(UserAnketa.email)


@router.message(F.text, StateFilter(UserAnketa.email))
async def make_anketa_(message: Message, state: FSMContext):
    """Получаем название города. Запрос на отправку номера кошелька"""
    logging.info(f'make_anketa_: {message.from_user.id}')
    await state.update_data(email=message.text)
    await message.answer(text=f'Отправьте адрес вашего электронного кошелька для вознаграждения, '
                              f'в случае выхода на работу.\n\n'
                              f'Также, вы можете воспользоваться реферальной программой и получать TON за приглашенных'
                              f' пользователей.\n\n'
                              f'/cancel для отмены',
                         reply_markup=pass_the_state())
    await state.set_state(UserAnketa.address)


@router.callback_query(F.data == 'create_wallet')
async def create_wallet(callback: CallbackQuery, state: FSMContext):
    """Видео-инструкция по созданию кошелька"""
    logging.info(f'create_wallet: {callback.message.from_user.id}')
    await callback.message.answer_video(video='BAACAgIAAxkBAAIG-mZ1D3n8x06fBosGaw290DPk6R91AAJlRwACuTmwS3Ys7U1g_Pa3NQQ',
                                        caption='Создайте кошелек по видео инструкции')
    await asyncio.sleep(5)
    await make_anketa_(message=callback.message, state=state)


@router.callback_query(F.data == 'pass_wallet')
async def pass_state(callback: CallbackQuery, state: FSMContext):
    """Пропустить ввод номера кошелька. Запрос на ссылку на вакансию"""
    logging.info(f'pass_state: {callback.message.from_user.id}')
    await callback.message.answer('Пришлите ссылку (номер) вакансии. Вы можете найти ее в Телеграм - '
                                  'канале @shoptalkrn',
                                  reply_markup=keyboard_cancel())
    await state.set_state(UserAnketa.Anketa)


@router.message(UserAnketa.address)
async def confirm_address(message: Message, state: FSMContext):
    """Получаем номер кошелька. С проверкой введенного номера кошелька на валидность"""
    logging.info(f'confirm_address: {message.from_user.id}')
    await state.update_data(address=message.text)
    if await check_valid_addr(message.text):
        link_wallet_test = f"https: // testnet.tonviewer.com / {message.text}"
        link_wallet = f"https://tonviewer.com/{message.text}"
        await message.answer(text=f'Ваш кошелек: <a href="{link_wallet}">{message.text}</a>\n\nПодтверждаете?',
                             parse_mode='html',
                             reply_markup=yes_or_no_addr(),
                             link_preview_options=LinkPreviewOptions(is_disabled=True))
    else:
        await message.answer(text=f'Данный адрес не валиден! Отправьте еще раз.',
                             reply_markup=keyboard_cancel())


@router.callback_query(F.data.startswith('address_'))
async def confirm_addres_yes_or_no(callback: CallbackQuery, state: FSMContext):
    """Подтверждение введенного номера кошелька"""
    logging.info(f'confirm_addres_y_n: {callback.from_user.id}')
    data = await state.get_data()
    answer = callback.data.split('_')
    if answer[1] == "confirm":
        await update_user_ton_addr(callback.from_user.id, data['address'])
        await callback.message.answer(text=f'Ваш кошелек был добавлен!',
                                      reply_markup=keyboards_main())
        await callback.message.answer('Пришлите ссылку на пост с вакансией из канала @shoptalkrn',
                                      reply_markup=keyboard_cancel())
        await state.set_state(UserAnketa.Anketa)
    else:
        await callback.message.answer(text=f'Ваш кошелек не был добавлен! Отправьте его снова!',
                                      reply_markup=keyboards_main())
        await state.set_state(UserAnketa.address)


@router.message(UserAnketa.Anketa)
async def get_anketa(message: Message, state: FSMContext):
    """Получение ссылки на пост с вакансией"""
    logging.info(f'get_anketa: {message.from_user.id}')
    await state.update_data(anketa=message.text)
    await state.set_state(default_state)
    await message.answer('Выберите профессию по вашей вакансии', reply_markup=keyboard_vacancy())


@router.callback_query(F.data.startswith("vacancy_"))
async def confirm_anketa(callback: CallbackQuery, state: FSMContext):
    """Получаем название профессии"""
    logging.info(f'confirm_anketa: {callback.message.from_user.id}')
    vacancy = callback.data.split('_')[1]
    await state.update_data(vacancy=vacancy)
    await callback.message.answer('Отправить анкету?', reply_markup=yes_or_no())
    await callback.answer()


@router.callback_query(F.data.startswith("linkanketa"))
async def confirm_anketa(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Подтверждение отправки анкеты"""
    logging.info(f'confirm_anketa: {callback.message.from_user.id}')
    # удаляем сообщение из которого получили апдейт
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    # получаем ответ пользователя из callback.data
    answer = callback.data.split('_')[1]
    # если отправка анкеты подтверждена
    if answer == 'confirm':
        # информируем что анкета отправляется
        msg = await callback.message.answer('Отправка анкеты...')
        # получаем количество строк из гугл-таблицы
        id_anketa = len(get_list_all_anketa())
        # обновляем данные пользователя
        await state.update_data(id_anketa=id_anketa)
        # обновляем словарь пользователя
        user_dict[callback.message.chat.id] = await state.get_data()
        # получаем данные из словаря пользователя
        anketa = user_dict[callback.message.chat.id]['anketa']
        name = user_dict[callback.message.chat.id]['name']
        phone = user_dict[callback.message.chat.id]['phone']
        city = user_dict[callback.message.chat.id]['city']
        vacancy = user_dict[callback.message.chat.id]['vacancy']
        email = user_dict[callback.message.chat.id]['email']
        # получаем данные о пользователе из БД по его id телеграм
        user = await get_user_from_id(user_id=callback.message.chat.id)
        # если у него есть реферер
        if user.referer_id != 0:
            # получаем данные о реферере по его id телеграм
            referer = await get_user_from_id(user_id=user.referer_id)
            id_telegram_referer = user.referer_id
            username_referer = referer.username
        # если реферера нет
        else:
            id_telegram_referer = 0
            username_referer = 'none'
        date_today = datetime.today().strftime('%d/%m/%Y')
        # отправляем данные в гугл таблицу
        append_anketa(id_anketa=id_anketa,
                      id_telegram_refer=callback.message.chat.id,
                      username_refer=callback.from_user.username,
                      id_telegram_referer=id_telegram_referer,
                      username_referer=username_referer,
                      name=name,
                      phone=phone,
                      city=city,
                      email=email,
                      link_post=anketa,
                      status="⚠️",
                      vacancy=vacancy,
                      date_anketa=date_today)
        # пауза 3 сек
        await asyncio.sleep(3)
        # удаляем сообщение, что данные отправляются
        await bot.delete_message(chat_id=callback.message.chat.id,
                                 message_id=msg.message_id)
        await callback.answer(text='Отлично, ваша анкета отправлена!',
                              show_alert=True)
        await callback.message.answer(text='Начисление TON произойдет через месяц после выхода на работу. \n\n'
                                           'Также вы можете воспользоваться реферальной программой и получать TON за'
                                           ' приглашенных пользователей')
        await callback.message.answer(text='Для оперативного начисления TON после месяца работы нажми на кнопку'
                                           ' "Хочу TON"',
                                      reply_markup=on_work(id_anketa=id_anketa))
        await state.set_state(default_state)
    else:
        await callback.message.answer(text='Вы отменили отправку анкеты',
                                      reply_markup=keyboards_main())
        await state.set_state(default_state)
    await callback.answer()


@router.callback_query(F.data.startswith('wishton_'))
async def want_ton(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """
    Пользователь запросил начисление TON. Подтверждение админом начисления
    """
    # информируем пользователя
    await callback.answer(text='Информация направлена администратору и после подтверждения вам будет начислено'
                               ' вознаграждение. Спасибо!',
                          show_alert=True)
    # удаляем у него сообщение
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    # обновляем данные словаря
    user_dict[callback.message.chat.id] = await state.get_data()
    # получаем ссылку на вакансию
    anketa = user_dict[callback.message.chat.id]['anketa']
    # получаем строку из гугл-таблицы
    id_anketa = user_dict[callback.message.chat.id]['id_anketa']
    info_anketa = get_list_anketa(id_anketa=id_anketa)
    # формируем строку вакансии
    vacancy = ''
    amount = 0
    if info_anketa[10] == 'merchandiser':
        vacancy = '#мерчандайзер'
        amount = 2000
    elif info_anketa[10] == 'mysteryShopper':
        vacancy = '#тайныйпокупатель'
        amount = 1000
    elif info_anketa[10] == 'consultant':
        vacancy = '#продавецконсультант'
        amount = 5000
    # обновляем статус пользователя на 'on_work
    await update_status(callback.from_user.id, UserStatus.on_work)
    # проходим по списку администраторов
    for admin_id in config.tg_bot.admin_ids.split(','):
        try:
            # информируем администратора о том что пользователь хочет получить вознаграждение
            await bot.send_message(chat_id=int(admin_id),
                                   text=f'Пользователь @{callback.from_user.username if callback.from_user.username else f"None-{callback.from_user.id}"}, откликнувшийся на вакансию:\n'
                                        f' {anketa} - {vacancy},'
                                        f' вышел на работу.\n'
                                        f'Подтвердите это изменение сведения в гугл таблице строка № {id_anketa}')
            await bot.send_message(chat_id=int(admin_id),
                                   text=f'Подтвердите начисление пользователю @{callback.from_user.username if callback.from_user.username else f"None-{callback.from_user.id}"} '
                                        f'{amount / 2} руб.',
                                   reply_markup=confirm(user_id=callback.message.chat.id, vacancy=info_anketa[10]))
        except:
            pass
    await state.set_state(default_state)
    await callback.answer()


@router.callback_query(F.data.startswith('confirm_pay_'))
async def transfer_pay_to(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Начисление TON подтверждено
    """
    logging.info(f'transfer_pay_to: {callback.data.split("_")[-1]}')
    # deleting the message from which update was called
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    # we get the telegram id of the user who requested the TON charge from callback.data
    user_to_pay = int(callback.data.split('_')[-1])
    vacancy = callback.data.split('_')[-1]
    # changing the status in the status cell for the user on '✅'
    update_status_anketa(status='✅', telegram_id=user_to_pay)
    # we get the wallet address for charging TON
    user_ton_addr = await get_user_ton_addr_by_id(user_to_pay)
    try:
        # получаем информацию о пользователе по его id телеграм
        user = await get_user_from_id(user_to_pay)
        # если статус его не равен "payed"
        if user.status != UserStatus.payed:
            amount = 0
            # получаем количество рублей для оплаты вознаграждения
            if vacancy == 'merchandiser':
                amount = 2000
            elif vacancy == 'mysteryShopper':
                amount = 1000
            elif vacancy == 'consultant':
                amount = 5000
            # получаем количество TON по курсу
            amount_ton = await get_ton_in_rub(amount=amount)
            # пользователю начисляем 50% от суммы
            amount_user_ton = amount_ton / 2
            # производим начисление
            transaction = await TonWallet.transfer(amount=amount_user_ton,
                                                   to_addr=user_ton_addr)
            # если статус платежа 'ok'
            if transaction == 'ok':
                # увеличиваем баланс пользователя
                await increase_ton_balance(tg_id=user_to_pay, s=amount_user_ton)
                # изменяем статус в гугл-таблице
                update_status_anketa(status='💰', telegram_id=user_to_pay)
                # изменяем статус в БД
                await update_status(user_to_pay, UserStatus.payed)
                # информируем админа об отправке вознаграждения
                await callback.message.answer(
                    f'✅ Пользователю @{await _get_username_from_id(user_to_pay)} отправлено <strong>{amount_user_ton} TON</strong>',
                    parse_mode='html')
                try:
                    # информируем пользователя, что ему начислено вознаграждение
                    await bot.send_message(chat_id=user_to_pay,
                                           text=f'Вам было отправлено {amount_user_ton} TON\n\n'
                                                f'Проверьте ваш кошелек'
                                                f' <a href="https://tonscan.org/address/{user_ton_addr}">кошелек.</a>',
                                           parse_mode='html',
                                           link_preview_options=LinkPreviewOptions(is_disabled=True))
                except:
                    pass
            # если статус нет денег
            elif transaction == 'not enough money':
                # отправляем админам информационное сообщение
                for admin_id in config.tg_bot.admin_ids.split(','):
                    try:
                        await bot.send_message(chat_id=int(admin_id),
                                               text=f'❗️Что-то пошло не так, и пользователю'
                                                    f' @{await _get_username_from_id(user_to_pay)} не пришло {amount_user_ton} TON,'
                                                    f' проверьте кошелек, скорее всего там недостаточно средств!')
                    except:
                        pass
            # если возникла ошибка
            elif transaction.startswith('error'):
                # информируем администраторов
                for admin_id in config.tg_bot.admin_ids.split(','):
                    try:
                        await bot.send_message(chat_id=int(admin_id),
                                               text=f'❗️Что-то пошло не так, и пользователю'
                                                    f' @{await _get_username_from_id(user_to_pay)} не пришло {amount_user_ton} TON,'
                                                    f' что-то пошло не так! Проверьте списание средств!')
                    except:
                        pass
            # получаем id телеграм реферера
            referer = user.referer_id
            # если он есть
            if referer:
                # начисляем 100% от суммы
                transaction = await TonWallet.transfer(amount=amount_ton,
                                                       to_addr=user_ton_addr)
                # если платеж прошел
                if transaction == 'ok':
                    # увеличиваем баланс
                    await increase_ton_balance(tg_id=user_to_pay, s=amount_ton)
                    # информируем реферера о вознагрождении
                    await bot.send_message(chat_id=referer,
                                           text=f'Вам отправлено <strong>{amount_ton} TON</strong> за приглашенного пользователя'
                                                f' @{await _get_username_from_id(user_to_pay)}',
                                           parse_mode='html')
                elif transaction == 'not enough money':
                    for admin_id in config.tg_bot.admin_ids.split(','):
                        try:
                            await bot.send_message(chat_id=int(admin_id),
                                                   text=f'❗️Что-то пошло не так, и пользователю @{await _get_username_from_id(referer)}'
                                                        f' за приглашенного @{await _get_username_from_id(user_to_pay)} не пришло {amount_ton} TON,'
                                                        f' проверьте кошелек, скорее всего там недостаточно средств!')
                        except:
                            pass
                elif transaction.startswith('error'):
                    for admin_id in config.tg_bot.admin_ids.split(','):
                        try:
                            await bot.send_message(chat_id=int(admin_id),
                                                   text=f'❗️Что-то пошло не так, и пользователю'
                                                        f' @{await _get_username_from_id(user_to_pay)} не пришло {amount_ton} TON,'
                                                        f' что-то пошло не так! Проверьте списание средств!')
                        except:
                            pass
        # пользователь уже получал вознаграждение по этой вакансии
        else:
            await callback.answer(text=f'Пользователь уже получил вознаграждение!',
                                  show_alert=True)
    except Exception as e:
        logging.error(f'ERROR: {e}')
    await callback.answer()


@router.callback_query(F.data.startswith('cancel_pay_'))
async def cancel_pay(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """
    Отмена начисления вознаграждения
    """
    logging.info(f'cancel_pay: {callback.data.split("_")[-1]}')
    await callback.answer()
    # id телеграм пользователя запросившего начисление TON
    user_to_pay = int(callback.data.split('_')[-1])
    # обновляем статус пользователя в БД
    await update_status(user_to_pay, UserStatus.not_payed)
    # информируем админа
    await callback.message.answer(text=f'❌ Пользователю @{await _get_username_from_id(user_to_pay)} оплата'
                                       f' не отправлена',
                                  parse_mode='html')
    try:
        # информируем пользователя
        await bot.send_message(chat_id=user_to_pay,
                               text='Оплата была не одобрена администрацией')
    except:
        pass
    # обновляем статус анкеты в гугл-таблице
    update_status_anketa(status='❌', telegram_id=user_to_pay)
