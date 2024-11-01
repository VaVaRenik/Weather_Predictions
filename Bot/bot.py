from aiogram import Bot
from aiogram import types
from aiogram import Router
from aiogram import Dispatcher
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from App.app import get_location_key_and_weather
from App.app import app
import asyncio
import threading
import os
from dotenv import load_dotenv


load_dotenv()

token = os.getenv("BOT_TOKEN")

bot = Bot(token=token)
router = Router()

user_data = {}

# Создание InLine Клавиатуры
add_stop_keyboard_builder = InlineKeyboardBuilder()
add_stop_keyboard_builder.button(text="Да", callback_data="add_stop_yes")
add_stop_keyboard_builder.button(text="Нет", callback_data="add_stop_no")
add_stop_keyboard: InlineKeyboardMarkup = add_stop_keyboard_builder.as_markup()


days_keyboard_builder = InlineKeyboardBuilder()
for i in range(1, 6):
    days_keyboard_builder.button(text=str(i), callback_data=f"days_{i}")
# Инофо
info_text = (
    "Что я умею:\n"
    "/start - Начать новый маршрут\n"
    "/restart - Начать заново\n"
    "Просто следуйте инструкциям после ввода команды!"
)


# Стартовое приветствие
@router.message(Command('start'))
async def start(message: types.Message):
    user_data[message.from_user.id] = {'stop_cities': []}  # Инициализация данных пользователя
    await message.reply("Привет! Я ваш личный помощник для планирования маршрутов и проверки погоды.\n"
                        "Введите начальную точку маршрута")


@router.message(Command('info'))
async def info(message: types.Message):
    await message.reply(info_text)


@router.message(Command("restart"))
async def restart(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    await bot.send_message(user_id, info_text)


# Ввод начальной точки
@router.message(lambda message: message.from_user.id in user_data and 'start_city' not in user_data[message.from_user.id])
async def get_start_city(message: types.Message):
    user_data[message.from_user.id]['start_city'] = message.text.strip()
    await message.reply("Отлично! Теперь введите конечную точку маршрута:")


# Ввод конечной точки
@router.message(lambda message: message.from_user.id in user_data and 'end_city' not in user_data[message.from_user.id])
async def get_end_city(message: types.Message):
    user_data[message.from_user.id]['end_city'] = message.text.strip()
    await message.reply("Хотите ли вы добавить промежуточные точки?", reply_markup=add_stop_keyboard)


@router.callback_query(lambda callback_query: callback_query.data in ['add_stop_yes', 'add_stop_no'])
async def process_add_stop(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        if callback_query.data == "add_stop_yes":
            await bot.send_message(user_id, "Введите промежуточную точку:")
        elif callback_query.data == "add_stop_no":
            await bot.send_message(user_id, "Маршрут готов, сейчас собираю данные о погоде...")
            await process_weather_info(user_id)  # Вызов функции для отправки погоды

        await callback_query.answer()  # Подтверждение обработки колбэка
    except TelegramBadRequest as e:
        if "query is too old" in str(e):
            # Игнорируем устаревший запрос
            pass
        else:
            raise e  # Пробрасываем другие исключения, чтобы их можно было отладить


# Ввод промежуточных точек
@router.message(lambda message: message.from_user.id in user_data and 'end_city' in user_data[message.from_user.id])
async def get_stop_city(message: types.Message):
    user_id = message.from_user.id
    user_data[user_id]['stop_cities'].append(message.text.strip())

    await message.reply("Хотите добавить еще одну промежуточную точку?", reply_markup=add_stop_keyboard)


# Функция для отправки информации о погоде и графиков
async def process_weather_info(user_id):
    try:
        data = user_data[user_id]
        start_city, end_city, stop_cities = data['start_city'], data['end_city'], data['stop_cities']

        # Получаем данные о погоде для начального и конечного города
        start_location_key, start_weather = get_location_key_and_weather(start_city)
        end_location_key, end_weather = get_location_key_and_weather(end_city)

        # Получаем данные для дополнительных городов
        stop_location_keys = []
        stop_weathers = []
        for stop_city in stop_cities:
            loc_key, weather = get_location_key_and_weather(stop_city)
            if loc_key is None or weather is None:
                await bot.send_message(user_id, "Не удается получить данные для дополнительных городов")
            else:
                stop_location_keys.append(loc_key)
                stop_weathers.append(weather)

        all_weathers = [start_weather] + stop_weathers + [end_weather]

        # Проверка погодных условий
        start_weather_bad = start_weather.is_weather_bad()
        end_weather_bad = end_weather.is_weather_bad()
        stop_weather_bad = any(weather.is_weather_bad() for weather in stop_weathers)

        if start_weather_bad or end_weather_bad or stop_weather_bad:
            await bot.send_message(user_id, "Есть плохие погодные условия на маршруте, рекомендуем выбрать другой день.")
        else:
            await bot.send_message(user_id, "Погода благоприятная на всем маршруте!")

        for weather in all_weathers:
            await bot.send_message(user_id, weather.display_weather_for_tg(),
                                   parse_mode="Markdown")

        local_url = f"http://127.0.0.1:5000/check-weather?start_city={start_city}&end_city={end_city}&stop_cities={','.join(stop_cities)}"
        await bot.send_message(user_id, f"Ссылка на графики: {local_url}")

    except Exception as e:
        await bot.send_message(user_id, f"Произошла ошибка: {e}")


# Запуск бота
async def run_bot():
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


def run_flask():
    app.run(port=5000)  # Запуск Flask на порту 5000


if __name__ == "__main__":
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Запуск Telegram бота в основном потоке
    asyncio.run(run_bot())

