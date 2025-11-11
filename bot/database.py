from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Boolean, select
from typing import Optional

# Database setup
engine = create_async_engine('sqlite+aiosqlite:///bot.db')
new_session = async_sessionmaker(engine, expire_on_commit=False)

# Base class for models
class Base(DeclarativeBase):
    pass

# User model
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

# UserInterest model (many-to-many relationship)
class UserInterest(Base):
    __tablename__ = 'user_interests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    interest = Column(String, nullable=False)

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Database helper functions
async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with new_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def create_user(telegram_id: int, username: Optional[str] = None, 
                    first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    async with new_session() as session:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

async def get_user_interests(user_id: int) -> list[str]:
    async with new_session() as session:
        result = await session.execute(
            select(UserInterest.interest).where(UserInterest.user_id == user_id)
        )
        return [row[0] for row in result.fetchall()]

async def save_user_interests(user_id: int, interests: list[str]):
    async with new_session() as session:
        # Remove existing interests
        existing = await session.execute(
            select(UserInterest).where(UserInterest.user_id == user_id)
        )
        for interest in existing.scalars().all():
            await session.delete(interest)
        
        # Add new interests
        for interest in interests:
            user_interest = UserInterest(user_id=user_id, interest=interest)
            session.add(user_interest)
        
        await session.commit()
