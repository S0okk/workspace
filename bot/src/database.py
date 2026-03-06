from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Database setup
engine = create_async_engine("sqlite+aiosqlite:///bot.db")
new_session = async_sessionmaker(engine, expire_on_commit=False)


# Base class for models
class Base(DeclarativeBase):
    pass


# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


# UserInterest model (many-to-many relationship)
class UserInterest(Base):
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    interest = Column(String, nullable=False)

    # Index for faster queries and unique constraint to prevent duplicates
    __table_args__ = (
        Index("ix_user_interest_unique", "user_id", "interest", unique=True),
    )


# UserReminder model - настройки напоминаний пользователя
class UserReminder(Base):
    __tablename__ = "user_reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    reminder_interval_days = Column(Integer, nullable=False, default=3)  # 1-7 дней
    last_reminder_date = Column(DateTime, nullable=True)
    next_reminder_date = Column(DateTime, nullable=True)
    is_enabled = Column(Boolean, default=True)


# StudyProgress model - история изучения
class StudyProgress(Base):
    __tablename__ = "study_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    topic = Column(String, nullable=False)  # Что изучил
    study_time_minutes = Column(
        Integer, nullable=False
    )  # Сколько времени потратил (в минутах)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)


# Daily model - Дневные вопросы/задания
class Daily(Base):
    __tablename__ = "dailies"

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)  # Текст вопроса/задания
    category = Column(
        String, nullable=False, default="general"
    )  # Категория (может быть связана с интересами)
    created_date = Column(DateTime, nullable=False, default=datetime.utcnow)


# UserDailyAnswer model - Ответы пользователей на дейлики
class UserDailyAnswer(Base):
    __tablename__ = "user_daily_answers"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    daily_id = Column(Integer, nullable=False, index=True)
    answer = Column(String, nullable=False)  # Ответ пользователя
    answered_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    next_repeat_date = Column(DateTime, nullable=False)  # Когда спросить снова
    repeat_count = Column(Integer, default=1)  # Сколько раз уже спрашивали

    __table_args__ = (
        Index("ix_user_daily_unique", "user_id", "daily_id", unique=True),
    )


# UserStreak model - День-стрик система
class UserStreak(Base):
    __tablename__ = "user_streaks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    current_streak = Column(Integer, default=0)  # Текущий стрик
    longest_streak = Column(Integer, default=0)  # Длиннейший стрик
    last_completed_date = Column(
        DateTime, nullable=True
    )  # Когда последний раз выполнил дейлики
    total_completed = Column(Integer, default=0)  # Всего выполнено дейликов


# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Database helper functions
async def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    async with new_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    async with new_session() as session:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
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
                reminder.next_reminder_date = datetime.utcnow() + timedelta(
                    days=interval_days
                )
                reminder.is_enabled = True
            else:
                reminder = UserReminder(
                    user_id=user_id,
                    reminder_interval_days=interval_days,
                    next_reminder_date=datetime.utcnow()
                    + timedelta(days=interval_days),
                    is_enabled=True,
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
        logger.error(
            f"Error updating reminder date for user {user_id}: {e}", exc_info=True
        )
        return False


async def get_users_due_for_reminder() -> list[UserReminder]:
    """Get all users who are due for a reminder."""
    async with new_session() as session:
        now = datetime.now()
        result = await session.execute(
            select(UserReminder).where(
                UserReminder.is_enabled.is_(True),
                UserReminder.next_reminder_date <= now,
            )
        )
        return list(result.scalars().all())


# ------------------ REMINDER + DAILIES INTEGRATION ------------------
async def prepare_reminder_for_user(
    user_id: int,
) -> Optional[tuple[UserReminder, Optional[Daily]]]:
    """Return the user's reminder settings and a Daily that should be asked now (or None).
    This combines selecting a daily together with reminder retrieval so the bot
    can ask the daily at the time of sending the reminder."""
    try:
        async with new_session() as session:
            now = datetime.utcnow()
            result = await session.execute(
                select(UserReminder).where(
                    UserReminder.user_id == user_id, UserReminder.is_enabled.is_(True)
                )
            )
            reminder = result.scalar_one_or_none()
            if not reminder:
                return None

            # Find a daily that the user hasn't answered yet or is due for repeat
            result2 = await session.execute(
                select(Daily)
                .outerjoin(
                    UserDailyAnswer,
                    (Daily.id == UserDailyAnswer.daily_id)
                    & (UserDailyAnswer.user_id == user_id),
                )
                .where(
                    (UserDailyAnswer.id.is_(None))
                    | (UserDailyAnswer.next_repeat_date <= now)
                )
                .distinct()
            )
            daily = result2.scalars().first()
            return reminder, daily
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error preparing reminder for user {user_id}: {e}", exc_info=True)
        return None


async def complete_reminder_and_optional_daily(
    user_id: int,
    daily_id: Optional[int] = None,
    answer: Optional[str] = None,
    repeat_interval_days: int = 1,
) -> bool:
    """Complete sending a reminder: update reminder dates and optionally
    save the user's answer to a daily. Commits both changes together.
    If `daily_id` and `answer` are provided, the user's answer is saved and
    the user's streak is updated."""
    try:
        async with new_session() as session:
            now = datetime.now()
            result = await session.execute(
                select(UserReminder).where(UserReminder.user_id == user_id)
            )
            reminder = result.scalar_one_or_none()
            if not reminder:
                return False

            # Update reminder timestamps
            reminder.last_reminder_date = now
            reminder.next_reminder_date = now + timedelta(
                days=reminder.reminder_interval_days
            )

            # Handle daily answer within the same transaction if provided
            if daily_id is not None and answer is not None:
                result2 = await session.execute(
                    select(UserDailyAnswer).where(
                        UserDailyAnswer.user_id == user_id,
                        UserDailyAnswer.daily_id == daily_id,
                    )
                )
                user_answer = result2.scalar_one_or_none()

                next_repeat_date = now + timedelta(days=repeat_interval_days)

                if user_answer:
                    user_answer.answer = answer
                    user_answer.answered_date = now
                    user_answer.next_repeat_date = next_repeat_date
                    user_answer.repeat_count = (user_answer.repeat_count or 0) + 1
                else:
                    user_answer = UserDailyAnswer(
                        user_id=user_id,
                        daily_id=daily_id,
                        answer=answer,
                        answered_date=now,
                        next_repeat_date=next_repeat_date,
                        repeat_count=1,
                    )
                    session.add(user_answer)

            await session.commit()

        # Update streak outside the DB transaction (uses its own session)
        if daily_id is not None and answer is not None:
            await update_streak(user_id)

        return True
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error completing reminder/daily for user {user_id}: {e}", exc_info=True
        )
        return False


# -------------------------------------------------------------------


# Study progress functions
async def save_study_progress(
    user_id: int, topic: str, study_time_minutes: int
) -> bool:
    """Save study progress entry."""
    try:
        async with new_session() as session:
            progress = StudyProgress(
                user_id=user_id,
                topic=topic,
                study_time_minutes=study_time_minutes,
                date=datetime.now(),
            )
            session.add(progress)
            await session.commit()
            return True
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error saving study progress for user {user_id}: {e}", exc_info=True
        )
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
            "total_time_minutes": total_time,
            "total_topics": total_topics,
            "entries": progress_list[-10:],  # Последние 10 записей
        }


# ==================== DAILIES FUNCTIONS ====================


async def get_or_create_daily(question: str, category: str = "general") -> int:
    """Get existing daily or create a new one. Returns daily_id."""
    try:
        async with new_session() as session:
            # Check if daily exists
            result = await session.execute(
                select(Daily).where(
                    Daily.question == question, Daily.category == category
                )
            )
            daily = result.scalar_one_or_none()

            if daily:
                return daily.id

            # Create new daily
            new_daily = Daily(question=question, category=category)
            session.add(new_daily)
            await session.commit()
            await session.refresh(new_daily)
            return new_daily.id
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error getting or creating daily: {e}", exc_info=True)
        raise


async def save_daily_answer(
    user_id: int, daily_id: int, answer: str, repeat_interval_days: int = 3
) -> bool:
    """Save or update user's answer to a daily question."""
    try:
        async with new_session() as session:
            result = await session.execute(
                select(UserDailyAnswer).where(
                    UserDailyAnswer.user_id == user_id,
                    UserDailyAnswer.daily_id == daily_id,
                )
            )
            user_answer = result.scalar_one_or_none()

            next_repeat_date = datetime.utcnow() + timedelta(days=repeat_interval_days)

            if user_answer:
                user_answer.answer = answer
                user_answer.answered_date = datetime.utcnow()
                user_answer.next_repeat_date = next_repeat_date
                user_answer.repeat_count += 1
            else:
                user_answer = UserDailyAnswer(
                    user_id=user_id,
                    daily_id=daily_id,
                    answer=answer,
                    next_repeat_date=next_repeat_date,
                    repeat_count=1,
                )
                session.add(user_answer)

            await session.commit()
            return True
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Error saving daily answer for user {user_id}: {e}", exc_info=True
        )
        return False


async def get_daily_to_answer(user_id: int) -> Optional[Daily]:
    """Get a daily question that user needs to answer (first time or due for repeat)."""
    try:
        async with new_session() as session:
            now = datetime.utcnow()

            # Find a daily that needs to be answered (either new or due for repeat)
            result = await session.execute(
                select(Daily)
                .outerjoin(
                    UserDailyAnswer,
                    (Daily.id == UserDailyAnswer.daily_id)
                    & (UserDailyAnswer.user_id == user_id),
                )
                .where(
                    (UserDailyAnswer.id.is_(None))  # New daily (no answer yet)
                    | (UserDailyAnswer.next_repeat_date <= now)  # Due for repeat
                )
                .distinct()
            )
            daily = result.scalars().first()
            return daily
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error getting daily to answer: {e}", exc_info=True)
        return None


async def get_all_dailies() -> list[Daily]:
    """Get all available dailies."""
    try:
        async with new_session() as session:
            result = await session.execute(select(Daily))
            return list(result.scalars().all())
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error getting all dailies: {e}", exc_info=True)
        return []


# ==================== STREAK FUNCTIONS ====================


async def get_or_create_streak(user_id: int) -> UserStreak:
    """Get user's streak or create a new one."""
    try:
        async with new_session() as session:
            result = await session.execute(
                select(UserStreak).where(UserStreak.user_id == user_id)
            )
            streak = result.scalar_one_or_none()

            if not streak:
                streak = UserStreak(user_id=user_id)
                session.add(streak)
                await session.commit()
                await session.refresh(streak)

            return streak
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error getting or creating streak: {e}", exc_info=True)
        raise


async def update_streak(user_id: int) -> dict:
    """Update user's streak. Returns streak info."""
    try:
        async with new_session() as session:
            result = await session.execute(
                select(UserStreak).where(UserStreak.user_id == user_id)
            )
            streak = result.scalar_one_or_none()

            if not streak:
                streak = UserStreak(user_id=user_id, current_streak=1, longest_streak=1)
                session.add(streak)
            else:
                last_completed = streak.last_completed_date
                now = datetime.utcnow()

                # Check if completed today
                if last_completed:
                    if (now.date() - last_completed.date()).days == 0:
                        # Already completed today
                        await session.commit()
                        return {
                            "current_streak": streak.current_streak,
                            "longest_streak": streak.longest_streak,
                            "is_new_day": False,
                        }
                    elif (now.date() - last_completed.date()).days == 1:
                        # Completed yesterday - continue streak
                        streak.current_streak += 1
                    else:
                        # Missed days - reset streak
                        streak.current_streak = 1
                else:
                    # First time
                    streak.current_streak = 1

                # Update longest streak
                if streak.current_streak > streak.longest_streak:
                    streak.longest_streak = streak.current_streak

            streak.last_completed_date = datetime.utcnow()
            streak.total_completed += 1

            await session.commit()

            return {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "is_new_day": True,
            }
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error updating streak: {e}", exc_info=True)
        raise


async def get_user_streak_info(user_id: int) -> dict:
    """Get user's current streak information."""
    try:
        async with new_session() as session:
            result = await session.execute(
                select(UserStreak).where(UserStreak.user_id == user_id)
            )
            streak = result.scalar_one_or_none()

            if not streak:
                return {"current_streak": 0, "longest_streak": 0, "total_completed": 0}

            return {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "total_completed": streak.total_completed,
            }
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error getting user streak info: {e}", exc_info=True)
        return {"current_streak": 0, "longest_streak": 0, "total_completed": 0}


# ==================== INITIALIZATION ====================


async def initialize_default_dailies():
    """Initialize default daily questions if not exist."""
    try:
        from messages import DAILY_QUESTIONS

        async with new_session() as session:
            result = await session.execute(select(Daily))
            existing_count = len(list(result.scalars().all()))

            if existing_count > 0:
                return  # Already initialized

            for category, questions in DAILY_QUESTIONS.items():
                for question in questions:
                    daily = Daily(question=question, category=category)
                    session.add(daily)

            await session.commit()
            import logging

            logger = logging.getLogger(__name__)
            logger.info("Default dailies initialized")
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error initializing default dailies: {e}", exc_info=True)
