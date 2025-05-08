import logging
from aiogram import Router, Bot, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, time
import re

from database import database
from keyboard import *

router = Router()
logger = logging.getLogger(__name__)

class AddPillStates(StatesGroup):
    entering_name = State()
    entering_time = State()

@router.message(F.text == "Добавить таблетку")
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
    try:
        hours, minutes = map(int, message.text.split(':'))
        time_obj = time(hour=hours, minute=minutes)
    except ValueError:
        await message.answer("Некорректное время! Введите снова:")
        return

    data = await state.get_data()
    await state.clear()

    async with database.transaction():
        query_pill = "INSERT INTO pills(user_id, name, time) VALUES(:user_id, :name, :time) RETURNING id"
        values_pill = {"user_id": message.from_user.id, "name": data['name'], "time": time_obj}
        pill_id = await database.execute(query=query_pill, values=values_pill)
        logger.info(f'Добавлена новая таблетка ID: {pill_id}')
        await message.answer(f"✅ {data['name']} добавлено на {message.text}", reply_markup=main_keyboard)

@router.message(F.text == "Список моих таблеток")
async def list_pills(message: Message):
    query = "SELECT name, time FROM pills WHERE user_id = :user_id"
    values = {"user_id": message.from_user.id}
    pills = await database.fetch_all(query=query, values=values)

    if not pills:
        await message.answer("У вас нет добавленных лекарств")
        return

    response = "Ваши лекарства:\n" + "\n".join(
        [f"💊 {pill.name} - {pill.time.strftime('%H:%M')}" for pill in pills]
    )
    await message.answer(response)

@router.callback_query()
async def confirm_pill(callback: types.CallbackQuery):
    logger.debug(f"Получен callback: {callback.data}")
    
    _, pill_id = callback.data.split("_")
    pill_id = int(pill_id)
    logger.info(f'Попытка подтверждения ID: {pill_id}')
    async with database.transaction():
        query = """
                UPDATE pills 
                SET last_taken = CURRENT_DATE
                WHERE id = :id
                AND (last_taken IS NULL OR last_taken < CURRENT_DATE)
                RETURNING name
                """
        values = {"id": pill_id}
        updated = await database.execute(query=query, values=values)
        if updated:
            await callback.message.edit_text(
                f"✅ Прием {updated} подтверждён",
                reply_markup=None
            )
            await callback.answer()
            logger.info(f'Подтверждение прием ID: {pill_id}')

async def check_pills(bot: Bot):
    now = datetime.now().time().replace(second=0, microsecond=0)
    logger.info(f'Проверка уведомлений в {now}')
    query = """
            SELECT * FROM pills 
            WHERE time <= :time 
            AND (last_taken IS NULL OR last_taken < CURRENT_DATE)
            AND (last_notified IS NULL OR last_notified <= NOW() - INTERVAL '5 minutes')
            """
    values = {"time": now}
    pills = await database.fetch_all(query=query, values=values)
    logger.info(f'Найдено {len(pills)} таблеток для уведомлений')

    for pill in pills:
        await bot.send_message(
            pill.user_id,
            f"⏰ Пора принять {pill.name}!",
            reply_markup=confirm_keyboard(pill.id)
        )
        query = "UPDATE pills SET last_notified = NOW() WHERE id = :id"
        values = {"id": pill.id}
        await database.execute(query=query, values=values)
        logger.info(f' Уведомление отправлено для таблетки ID: {pill.id}')


pass #Добавить кнопку удалить таблетку