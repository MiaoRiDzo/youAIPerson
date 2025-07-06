import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from .database.engine import create_tables, AsyncSessionLocal
from .handlers.user_commands import router as user_router


async def main():
    """Main function to start the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Initialize bot and dispatcher with FSM storage
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Add middleware for database session injection
    @dp.update.middleware()
    async def database_middleware(handler, event, data):
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)
    
    # Register routers
    dp.include_router(user_router)
    
    # Create database tables
    print("🗄️  Creating database tables...")
    await create_tables()
    print("✅ Database tables created successfully!")
    
    # Get bot info
    bot_info = await bot.get_me()
    print(f"🤖 Bot started: @{bot_info.username}")
    print("📱 Bot is ready to receive messages...")
    print(f"💾 FSM storage initialized")
    
    # Start polling
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Error during polling: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 