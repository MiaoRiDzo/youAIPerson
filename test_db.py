#!/usr/bin/env python3
"""
Test script for database functionality
"""

import asyncio
import sys
import os

# Добавляем корневую папку в путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.engine import create_tables, AsyncSessionLocal
from app.database.models import User
from sqlalchemy import select


async def test_database():
    """Test database functionality"""
    print("🧪 Testing database functionality...")
    
    try:
        # Create tables
        await create_tables()
        print("✅ Tables created successfully")
        
        # Test session creation
        async with AsyncSessionLocal() as session:
            print("✅ Session created successfully")
            
            # Test query
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            print(f"✅ Query executed successfully. Found {len(users)} users")
            
        print("🎉 All database tests passed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_database()) 