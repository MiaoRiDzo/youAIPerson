from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import json

from app.database.models import User, Hook
from app.services.gemini_service import analyze_and_manage_hooks, generate_assistant_reply

router = Router()

# --- FSM States for Role Management ---
class RoleStates(StatesGroup):
    waiting_for_new_role = State()

# --- Helper Functions ---
def parse_expires_at(expires_at_str: str | None) -> datetime | None:
    """Parse ISO 8601 string to timezone-aware datetime"""
    if not expires_at_str:
        return None
    try:
        # Parse ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
        dt = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        return dt
    except ValueError:
        print(f"❌ Invalid expires_at format: {expires_at_str}")
        return None

def format_hook_with_expiry(hook: Hook) -> str:
    """Format hook text with expiration date if available"""
    if hook.expires_at:
        return f"• {hook.text} (истекает: {hook.expires_at.strftime('%d.%m.%Y %H:%M')})"
    return f"• {hook.text}"

def convert_google_api_object(obj):
    """Recursively convert Google API objects to Python structures"""
    if hasattr(obj, 'items'):  # MapComposite
        return {key: convert_google_api_object(value) for key, value in obj.items()}
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):  # RepeatedComposite
        return [convert_google_api_object(item) for item in obj]
    else:
        return obj

# --- /start Command Handler ---
@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        # Check if user exists
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
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

# --- General Message Handler ---
@router.message(F.text & ~F.text.startswith('/'))
async def handle_message(
    message: Message,
    session: AsyncSession
):
    """Handle general user messages and update memory"""
    user_id = message.from_user.id
    
    # Get or create user
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()
    
    # Get user's hooks (excluding expired ones)
    result = await session.execute(
        select(Hook)
        .where(Hook.user_id == user_id)
        .where(
            (Hook.expires_at.is_(None)) | 
            (Hook.expires_at > datetime.now(timezone.utc))
        )
    )
    existing_hooks = [hook.text for hook in result.scalars().all()]
    
    # Analyze message and manage hooks
    function_call = await analyze_and_manage_hooks(
        message.text,
        existing_hooks,
        role_prompt=user.role_prompt
    )
    
    if function_call:
        try:
            # Convert Google API objects to Python dict using recursive conversion
            args = convert_google_api_object(function_call.args)
            print(f"[FUNCTION CALL ARGS]: {json.dumps(args, ensure_ascii=False, indent=2)}")
            
            # Process hooks_to_add
            if 'hooks_to_add' in args:
                for hook_data in args['hooks_to_add']:
                    if isinstance(hook_data, dict):
                        text = hook_data.get('text')
                        expires_at_str = hook_data.get('expires_at')
                    else:
                        text = hook_data
                        expires_at_str = None
                    
                    if text:
                        expires_at = parse_expires_at(expires_at_str)
                        new_hook = Hook(
                            user_id=user_id,
                            text=text,
                            expires_at=expires_at
                        )
                        session.add(new_hook)
                        print(f"[ADDED HOOK]: {text} (expires: {expires_at})")
            
            # Process hooks_to_update
            if 'hooks_to_update' in args:
                for update_data in args['hooks_to_update']:
                    old_text = update_data.get('old_hook_text')
                    new_text = update_data.get('new_hook_text')
                    expires_at_str = update_data.get('expires_at')
                    
                    if old_text and new_text:
                        result = await session.execute(
                            select(Hook).where(
                                Hook.user_id == user_id,
                                Hook.text == old_text
                            )
                        )
                        hook = result.scalar_one_or_none()
                        if hook:
                            hook.text = new_text
                            hook.expires_at = parse_expires_at(expires_at_str)
                            print(f"[UPDATED HOOK]: {old_text} -> {new_text}")
            
            # Process hooks_to_delete
            if 'hooks_to_delete' in args:
                for text_to_delete in args['hooks_to_delete']:
                    result = await session.execute(
                        select(Hook).where(
                            Hook.user_id == user_id,
                            Hook.text == text_to_delete
                        )
                    )
                    hook = result.scalar_one_or_none()
                    if hook:
                        await session.delete(hook)
                        print(f"[DELETED HOOK]: {text_to_delete}")
            
            await session.commit()
            print(f"✅ Database updated successfully for user {user_id}")
            
        except Exception as e:
            print(f"❌ Error processing function call: {e}")
            await session.rollback()
    
    # Generate and send response
    response_text = await generate_assistant_reply(message.text, existing_hooks)
    await message.answer(response_text)

# --- /clean Command Handler ---
@router.message(Command("clean"))
async def clean_chat_history(message: Message):
    """Clear chat history for the user"""
    await message.answer("✅ История чата очищена. Начинаем новый диалог!")

# --- /hooks Command Handler ---
@router.message(Command("hooks"))
async def show_hooks(message: Message, session: AsyncSession):
    """Show user's non-expired hooks"""
    user_id = message.from_user.id
    
    # Get non-expired hooks
    result = await session.execute(
        select(Hook)
        .where(Hook.user_id == user_id)
        .where(
            (Hook.expires_at.is_(None)) | 
            (Hook.expires_at > datetime.now(timezone.utc))
        )
    )
    hooks = result.scalars().all()
    
    if not hooks:
        await message.answer("📝 У вас пока нет сохранённых фактов. Я буду запоминать информацию о вас в процессе общения.")
        return
    
    # Format hooks list
    hooks_text = "📝 Ваши сохранённые факты:\n\n"
    for hook in hooks:
        hooks_text += format_hook_with_expiry(hook) + "\n"
    
    hooks_text += "\n💡 Для изменения или удаления фактов просто напишите об этом в чате."
    
    await message.answer(hooks_text)

# --- /role Command Handler ---
@router.message(Command("role"))
async def show_role(message: Message, session: AsyncSession):
    """Show user's current role and provide management options"""
    user_id = message.from_user.id
    
    # Get user
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.role_prompt:
        role_text = "🎭 У вас пока не установлена роль."
    else:
        role_text = f"🎭 Ваша текущая роль:\n\n{user.role_prompt}"
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Очистить роль", callback_data="clear_role"),
                InlineKeyboardButton(text="Изменить роль", callback_data="edit_role")
            ]
        ]
    )
    
    await message.answer(role_text, reply_markup=keyboard)

# --- Callback Handlers ---
@router.callback_query(F.data == "clear_role")
async def clear_role_callback(callback: CallbackQuery, session: AsyncSession):
    """Clear user's role"""
    user_id = callback.from_user.id
    
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        user.role_prompt = None
        await session.commit()
    
    await callback.message.edit_text("✅ Роль очищена.")

@router.callback_query(F.data == "edit_role")
async def edit_role_callback(callback: CallbackQuery, state: FSMContext):
    """Start role editing process"""
    await state.set_state(RoleStates.waiting_for_new_role)
    await callback.message.edit_text("✍️ Напишите вашу новую роль. Например:\n\n• 'Я программист Python'\n• 'Я студент медицинского вуза'\n• 'Я люблю путешествовать и фотографировать'")

# --- FSM Message Handler for Role Editing ---
@router.message(RoleStates.waiting_for_new_role)
async def handle_new_role(message: Message, session: AsyncSession, state: FSMContext):
    """Handle new role input"""
    user_id = message.from_user.id
    new_role = message.text
    
    # Get or create user
    result = await session.execute(
        select(User).where(User.user_id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
    
    user.role_prompt = new_role
    await session.commit()
    
    await state.clear()
    await message.answer(f"✅ Роль обновлена:\n\n{new_role}") 