from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timedelta
import re

from pyrogram.types import CallbackQuery

from database import database
from keyboard import confirm_keyboard

router = Router()

class AddPillStates(StatesGroup):
    entering_name = State()
    entering_time = State()

@router.message(Text(text="Добавить таблетку"))
async def add_pill_start(message: Message, state: FSMContext):
    await state.set_state(AddPillStates.entering_name)
    await message.answer("Введите название лекарства:")

@router.message(AddPillStates.entering_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddPillStates.entering_time)
    await message.answer("Введите время приема в формате ЧЧ:ММ:")

@router.message(AddPillStates.entering_time)
async def process_time(message: Message, state: FSMContext):
    if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', message.text):
        await message.answer("Неверный формат времени! Введите снова:")
        return

    data = await state.get_data()
    await state.clear()

    async with database.transaction():
        query_user = "INSERT INTO users(user_id) VALUES(:user_id) ON CONFLICT DO NOTHING"
        values_user = {"user_id": message.from_user.id}
        await database.execute(query=query_user, values=values_user)

        query_pill = "INSERT INTO pills(:user_id, name, time) VALUES(:user_id, :name, :time)"
        values_pill = {"user_id": message.from_user.id, "name": data['name'], "time": message.text}
        await database.execute(query=query_pill, values=values_pill)

        await message.answer(f"✅ {data['name']} добавлено на {message.text}", reply_markup=main_keyboard)

@router.message(Text(text="Список моих таблеток"))
async def list_pills(message: Message):
    query = "SELECT name, time FROM pills WHERE user_id = :user_id"
    values = {"user_id": message.from_user.id}
    pills = await database.fetch_all(query=query, values=values)

    if not pills:
        await message.answer("У вас нет добавленных лекарств")
        return

    response = "Ваши лекарства:\n" + "\n".join(
        [f"💊 {pill.name} - {pill.time}" for pill in pills]
    )
    await message.answer(response)

@router.callback_query(Text(text="confirm"))
async def confirm_pill(callback: CallbackQuery):
    query = "UPDATE pills SET is_taken = TRUE WHERE user_id = :user_id"
    values = {"user_id": callback.from_user.id}
    await database.execute(query=query, values=values)
    await callback.message.delete()
    await callback.answer("Прием таблетки подтвержден!")

async def check_pills(bot: Bot):
    now = datetime.now().strftime("%H:%M")
    query = "SELECT * FROM pills WHERE time = :time AND (last_notified IS NULL OR last_notified < NOW() - INTERVAL '5 minutes') AND is_taken = FALSE"
    values = {"time": now}
    pills = await database.fetch_all(query=query, values=values)

    for pill in pills:
        await bot.send_message(
            pill.user_id,
            f"⏰ Пора принять {pill.name}!",
            reply_markup=confirm_keyboard
        )
        query = "UPDATE pills SET last_notified = NOW() WHERE id = :id"
        values = {"id": pill.id}
        await database.execute(query=query, values=values)
