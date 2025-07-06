import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from .database.engine import create_tables
from .handlers.user_commands import router as user_router


async def main():
    """Main function to start the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get bot token from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Initialize bot and dispatcher
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    
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
    
    # Start polling
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Error during polling: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 