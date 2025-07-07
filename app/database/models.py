from sqlalchemy import BigInteger, String, ForeignKey, func, TIMESTAMP, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class User(Base):
    """User model for storing Telegram user information"""
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP, 
        server_default=func.now(),
        nullable=False
    )
    
    hooks: Mapped[list["Hook"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"User(user_id={self.user_id}, username={self.username}, first_name={self.first_name})"


class BotPersonality(Base):
    """Bot personality model for storing bot's personality settings"""
    __tablename__ = "bot_personality"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    personality_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP, 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP, 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    user: Mapped["User"] = relationship()
    
    def __repr__(self) -> str:
        return f"BotPersonality(id={self.id}, user_id={self.user_id}, personality_prompt='{self.personality_prompt[:50] if self.personality_prompt else None}...')"


class Hook(Base):
    """Hook model for storing user memory facts"""
    __tablename__ = "hooks"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(
        TIMESTAMP, 
        server_default=func.now(),
        nullable=False
    )
    
    user: Mapped["User"] = relationship(back_populates="hooks")
    
    def __repr__(self) -> str:
        return f"Hook(id={self.id}, user_id={self.user_id}, text='{self.text[:50]}...')" 