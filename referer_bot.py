import asyncio
import logging
import traceback
from aiogram.types import FSInputFile
from aiogram.types import ErrorEvent
from aiogram import Bot, Dispatcher
from config_data.config import Config, load_config
from handlers import handler_user, handler_scheduler, other_handlers
from handlers.scheduler import send_ton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Инициализируем logger
logger = logging.getLogger(__name__)


# Функция конфигурирования и запуска бота
async def main():
    # create_table_users()
    # Конфигурируем логирование
    logging.basicConfig(
        level=logging.INFO,
        filename="py_log.log",
        filemode='w',
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Выводим в консоль информацию о начале запуска бота
    logger.info('Starting bot')

    # Загружаем конфиг в переменную config
    config: Config = load_config()

    # Инициализируем бот и диспетчер
    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher()
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    # каждый день
    scheduler.add_job(send_ton, 'cron', hour=10, minute=0, args=(bot,))
    # scheduler.add_job(send_ton, 'cron', hour=15, minute=55, args=(bot,))
    scheduler.start()
    # Регистрируем router в диспетчере
    dp.include_router(handler_user.router)
    dp.include_router(handler_scheduler.router)
    dp.include_router(other_handlers.router)


    @dp.error()
    async def error_handler(event: ErrorEvent):
        logger.critical("Критическая ошибка: %s", event.exception, exc_info=True)
        await bot.send_message(chat_id=843554518,
                               text=f'{event.exception}')
        formatted_lines = traceback.format_exc()
        text_file = open('error.txt', 'w')
        text_file.write(str(formatted_lines))
        text_file.close()
        await bot.send_document(chat_id=843554518,
                                document=FSInputFile('error.txt'))
    # Пропускаем накопившиеся update и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
