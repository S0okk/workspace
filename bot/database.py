from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Boolean, select, delete, Index, DateTime
from typing import Optional
from datetime import datetime, timedelta

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
    user_id = Column(Integer, nullable=False, index=True)
    interest = Column(String, nullable=False)
    
    # Index for faster queries and unique constraint to prevent duplicates
    __table_args__ = (
        Index('ix_user_interest_unique', 'user_id', 'interest', unique=True),
    )

# UserReminder model - настройки напоминаний пользователя
class UserReminder(Base):
    __tablename__ = 'user_reminders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    reminder_interval_days = Column(Integer, nullable=False, default=3)  # 1-7 дней
    last_reminder_date = Column(DateTime, nullable=True)
    next_reminder_date = Column(DateTime, nullable=True)
    is_enabled = Column(Boolean, default=True)

# StudyProgress model - история изучения
class StudyProgress(Base):
    __tablename__ = 'study_progress'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    topic = Column(String, nullable=False)  # Что изучил
    study_time_minutes = Column(Integer, nullable=False)  # Сколько времени потратил (в минутах)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)

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

async def save_user_interests(user_id: int, interests: list[str]) -> bool:
    """Save user interests to database. Replaces existing interests with new ones.
    Returns True if successful, False otherwise."""
    try:
        async with new_session() as session:
            # Remove existing interests using bulk delete (more efficient)
            await session.execute(
                delete(UserInterest).where(UserInterest.user_id == user_id)
            )
            # Flush to ensure delete is executed before adding new records
            # This prevents unique constraint violations when re-adding the same interests
            await session.flush()
            
            # Add new interests
            if interests:
                for interest in interests:
                    user_interest = UserInterest(user_id=user_id, interest=interest)
                    session.add(user_interest)
            
            await session.commit()
            return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving interests for user {user_id}: {e}", exc_info=True)
        return False

# Reminder functions
async def get_user_reminder(user_id: int) -> Optional[UserReminder]:
    """Get user reminder settings."""
    async with new_session() as session:
        result = await session.execute(
            select(UserReminder).where(UserReminder.user_id == user_id)
        )
        return result.scalar_one_or_none()

async def create_or_update_reminder(user_id: int, interval_days: int) -> bool:
    """Create or update user reminder settings."""
    try:
        async with new_session() as session:
            result = await session.execute(
                select(UserReminder).where(UserReminder.user_id == user_id)
            )
            reminder = result.scalar_one_or_none()
            
            if reminder:
                reminder.reminder_interval_days = interval_days
                reminder.next_reminder_date = datetime.utcnow() + timedelta(days=interval_days)
                reminder.is_enabled = True
            else:
                reminder = UserReminder(
                    user_id=user_id,
                    reminder_interval_days=interval_days,
                    next_reminder_date=datetime.utcnow() + timedelta(days=interval_days),
                    is_enabled=True
                )
                session.add(reminder)
            
            await session.commit()
            return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving reminder for user {user_id}: {e}", exc_info=True)
        return False

async def update_reminder_date(user_id: int, new_date: datetime) -> bool:
    """Update last and next reminder dates."""
    try:
        async with new_session() as session:
            result = await session.execute(
                select(UserReminder).where(UserReminder.user_id == user_id)
            )
            reminder = result.scalar_one_or_none()
            if reminder:
                reminder.last_reminder_date = datetime.utcnow()
                reminder.next_reminder_date = new_date
                await session.commit()
                return True
            return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating reminder date for user {user_id}: {e}", exc_info=True)
        return False

async def get_users_due_for_reminder() -> list[UserReminder]:
    """Get all users who are due for a reminder."""
    async with new_session() as session:
        now = datetime.utcnow()
        result = await session.execute(
            select(UserReminder).where(
                UserReminder.is_enabled.is_(True),
                UserReminder.next_reminder_date <= now
            )
        )
        return list(result.scalars().all())

# Study progress functions
async def save_study_progress(user_id: int, topic: str, study_time_minutes: int) -> bool:
    """Save study progress entry."""
    try:
        async with new_session() as session:
            progress = StudyProgress(
                user_id=user_id,
                topic=topic,
                study_time_minutes=study_time_minutes,
                date=datetime.utcnow()
            )
            session.add(progress)
            await session.commit()
            return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving study progress for user {user_id}: {e}", exc_info=True)
        return False

async def get_user_study_stats(user_id: int) -> dict:
    """Get user study statistics."""
    async with new_session() as session:
        result = await session.execute(
            select(StudyProgress).where(StudyProgress.user_id == user_id)
        )
        progress_list = list(result.scalars().all())
        
        total_time = sum(p.study_time_minutes for p in progress_list)
        total_topics = len(progress_list)
        
        return {
            'total_time_minutes': total_time,
            'total_topics': total_topics,
            'entries': progress_list[-10:]  # Последние 10 записей
        }
