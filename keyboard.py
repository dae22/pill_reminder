from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить таблетку"),
         KeyboardButton(text="Список моих таблеток")]
    ],
    resize_keyboard=True
)

confirm_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принял", callback_data="confirm")]
    ]
)
