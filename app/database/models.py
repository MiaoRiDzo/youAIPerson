from sqlalchemy import BigInteger, String, TIMESTAMP, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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
    
    def __repr__(self) -> str:
        return f"User(user_id={self.user_id}, username={self.username}, first_name={self.first_name})" 