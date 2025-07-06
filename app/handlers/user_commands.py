from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import User, Hook
from ..database.engine import AsyncSessionLocal
from ..services.gemini_service import analyze_and_manage_hooks, generate_assistant_reply

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


@router.message(Command("hooks"))
async def cmd_hooks(message: Message):
    """Show user's memory hooks"""
    try:
        user_id = message.from_user.id
        
        async with AsyncSessionLocal() as session:
            # Get user with hooks
            stmt = select(User).options(selectinload(User.hooks)).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                await message.answer("Пользователь не найден в базе данных.")
                return
            
            if not user.hooks:
                await message.answer("У вас пока нет сохраненных фактов в памяти.")
                return
            
            # Format hooks for display
            hooks_text = "📝 Ваши сохраненные факты:\n\n"
            for i, hook in enumerate(user.hooks, 1):
                hooks_text += f"{i}. {hook.text}\n"
            
            await message.answer(hooks_text)
            
    except Exception as e:
        print(f"❌ Ошибка при получении хуков: {e}")
        await message.answer("Произошла ошибка при получении данных.")


@router.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message):
    """Handle text messages and manage user memory hooks, always reply as assistant"""
    try:
        user_id = message.from_user.id
        message_text = message.text
        
        # Get user and their hooks
        async with AsyncSessionLocal() as session:
            # Query user with hooks
            stmt = select(User).options(selectinload(User.hooks)).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                await message.answer("Пользователь не найден в базе данных.")
                return
            
            # Get existing hooks
            existing_hooks = [hook.text for hook in user.hooks]
            
            # 1. Обновляем память через Gemini
            function_call = await analyze_and_manage_hooks(message_text, existing_hooks)
            if function_call and hasattr(function_call, 'name') and function_call.name == "manage_user_memory_hooks":
                args = function_call.args
                # Add new hooks
                if "hooks_to_add" in args and args["hooks_to_add"]:
                    for hook_text in args["hooks_to_add"]:
                        new_hook = Hook(user_id=user_id, text=hook_text)
                        session.add(new_hook)
                        print(f"✅ Добавлен новый хук: {hook_text}")
                # Delete hooks
                if "hooks_to_delete" in args and args["hooks_to_delete"]:
                    for hook_text in args["hooks_to_delete"]:
                        stmt = delete(Hook).where(Hook.user_id == user_id, Hook.text == hook_text)
                        await session.execute(stmt)
                        print(f"🗑️ Удален хук: {hook_text}")
                # Update hooks
                if "hooks_to_update" in args and args["hooks_to_update"]:
                    for update_item in args["hooks_to_update"]:
                        old_text = update_item["old_hook_text"]
                        new_text = update_item["new_hook_text"]
                        stmt = update(Hook).where(
                            Hook.user_id == user_id, 
                            Hook.text == old_text
                        ).values(text=new_text)
                        await session.execute(stmt)
                        print(f"🔄 Обновлен хук: '{old_text}' → '{new_text}'")
                await session.commit()
                print(f"💾 Изменения сохранены для пользователя {user_id}")
            
            # 2. Генерируем ответ ассистента с учетом памяти
            reply = await generate_assistant_reply(message_text, [hook.text for hook in user.hooks])
            await message.answer(reply)
    except Exception as e:
        print(f"❌ Ошибка при обработке сообщения: {e}")
        await message.answer("[Внутренняя ошибка бота. Попробуйте позже или обратитесь к администратору.]") 