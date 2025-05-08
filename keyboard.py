from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить таблетку"),
         KeyboardButton(text="Список моих таблеток"),
         KeyboardButton(text="Удалить таблетку")]
    ],
    resize_keyboard=True
)

def confirm_keyboard(pill_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Принял",
        callback_data=f'confirm_{pill_id}'
    )
    return builder.as_markup()
