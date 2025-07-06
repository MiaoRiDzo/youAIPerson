from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import User
from ..database.engine import AsyncSessionLocal

# Create router for user commands
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        # Open async session
        async with AsyncSessionLocal() as session:
            # Check if user exists
            stmt = select(User).where(User.user_id == user_id)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create new user
                new_user = User(
                    user_id=user_id,
                    username=username,
                    first_name=first_name
                )
                session.add(new_user)
                await session.commit()
                print(f"✅ Новый пользователь зарегистрирован: {first_name} (ID: {user_id})")
            else:
                print(f"👤 Пользователь уже существует: {first_name} (ID: {user_id})")
            
            # Send welcome message
            welcome_text = f"Привет, {first_name}! Я бот с продвинутой системой памяти. Рад нашему знакомству!"
            await message.answer(welcome_text)
    
    except Exception as e:
        print(f"❌ Ошибка в команде /start: {e}")
        await message.answer("Произошла ошибка при обработке команды. Попробуйте позже.")


@router.message(Command("clean"))
async def cmd_clean(message: Message):
    """Handle /clean command (placeholder for future implementation)"""
    await message.answer("Функция очистки пока в разработке!")


@router.message(F.text)
async def handle_text(message: Message):
    """Handle all text messages (placeholder for future implementation)"""
    await message.answer("Получил ваше сообщение! Функции обработки текста пока в разработке.") 