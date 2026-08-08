import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class SupportFlow(StatesGroup):
    waiting_for_name = State()
    waiting_for_query = State()

def get_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Ask AI Assistant", callback_data="ask_ai")],
            [InlineKeyboardButton(text="📅 Book Consultation", callback_data="book_consult")],
            [InlineKeyboardButton(text="ℹ️ About Us", callback_data="about")]
        ]
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"👋 Welcome, {message.from_user.first_name}!\n\n"
        "I am an **AI-Powered Customer Assistant**.\n"
        "How can I help you today?"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "about")
async def process_about(callback: types.CallbackQuery):
    about_text = (
        "<b>Automated Business Bot v2.4</b>\n\n"
        "• Powered by OpenAI GPT-4 Turbo\n"
        "• Asynchronous Python Backend (aiogram 3.x)\n"
        "• Integrated Webhooks & State Management"
    )
    await callback.message.edit_text(about_text, parse_mode="HTML", reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(F.data == "book_consult")
async def start_consultation_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SupportFlow.waiting_for_name)
    await callback.message.answer("Please enter your Full Name to register for a consultation:")
    await callback.answer()

@dp.message(SupportFlow.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SupportFlow.waiting_for_query)
    await message.answer("Thank you! Now please describe your inquiry or business goal:")

@dp.message(SupportFlow.waiting_for_query)
async def process_query(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = user_data.get("name")
    query = message.text
    await state.clear()
    
    confirmation = (
        "✅ <b>Consultation Request Received!</b>\n\n"
        f"<b>Name:</b> {full_name}\n"
        f"<b>Inquiry:</b> {query}\n\n"
        "Our team will contact you shortly."
    )
    await message.answer(confirmation, parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.callback_query(F.data == "ask_ai")
async def prompt_ai_question(callback: types.CallbackQuery):
    await callback.message.answer("Ask me anything! Type your question directly in the chat:")
    await callback.answer()

@dp.message()
async def handle_ai_chat(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional corporate AI assistant."},
                {"role": "user", "content": message.text}
            ],
            max_tokens=300
        )
        await message.reply(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        await message.reply("Sorry, I encountered an issue processing your request.")

async def main():
    logging.info("Starting Telegram Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
