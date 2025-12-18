import os
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from database import (
    init_db, get_user_by_telegram_id, create_user, get_user_interests, save_user_interests,
    get_user_reminder, create_or_update_reminder, update_reminder_date, get_users_due_for_reminder,
    save_study_progress, get_user_study_stats
)
from messages import INTERESTS_LIST, format_interests_list, format_available_interests

load_dotenv()

# Enable logging to both console and file
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def format_user_config(db_user, interests: list[str]) -> str:
    """Format user configuration information."""
    config_text = "⚙️ **Ваши настройки:**\n\n"
    config_text += f"**ID пользователя:** {db_user.id}\n"
    config_text += f"**Telegram ID:** {db_user.telegram_id}\n"
    config_text += f"**Имя:** {db_user.first_name or 'Не указано'}\n"
    config_text += f"**Фамилия:** {db_user.last_name or 'Не указано'}\n"
    config_text += f"**Username:** @{db_user.username if db_user.username else 'Не указано'}\n"
    config_text += f"**Статус:** {'Активен' if db_user.is_active else 'Неактивен'}\n\n"
    
    config_text += "**Ваши интересы:**\n"
    if interests:
        for i, interest in enumerate(interests, 1):
            config_text += f"{i}. {interest}\n"
    else:
        config_text += "Интересы не выбраны. Используйте /interests для выбора.\n"
    
    return config_text


def get_main_keyboard():
    """Create main keyboard with Help and Config buttons"""
    keyboard = [
        [
            InlineKeyboardButton("📖 Помощь", callback_data="help"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="config")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.message.from_user
    
    try:
        # Adding new user to database or updating existing one
        db_user = await get_user_by_telegram_id(user.id)
        is_new_user = False
        
        if not db_user:
            db_user = await create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"New user registered: {user.id} (@{user.username})")
            is_new_user = True
        
        if is_new_user:
            welcome_text = f"""🎉 Добро пожаловать, {user.first_name or 'друг'}!

Я дейлик бот - помогу тебе найти единомышленников и интересные темы для обсуждения.

**Для начала работы нужно выбрать интересы!**

Это поможет мне лучше понять, чем ты увлекаешься. 👇"""
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=get_main_keyboard()
            )
            
            # Автоматически показываем выбор интересов для новых пользователей
            await asyncio.sleep(1)  # Небольшая задержка для лучшего UX
            await show_interests_selection(update, context, db_user)
        else:
            # Проверяем, есть ли интересы у пользователя
            interests = await get_user_interests(db_user.id)
            if not interests:
                welcome_text = f"""👋 С возвращением, {user.first_name or 'друг'}!

Похоже, ты еще не выбрал свои интересы. Давай это исправим! 👇"""
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=get_main_keyboard()
                )
                await asyncio.sleep(1)
                await show_interests_selection(update, context, db_user)
            else:
                welcome_text = f"""👋 С возвращением, {user.first_name or 'друг'}!

Используй команды для навигации:
/help - Справка по командам
/config - Настройки профиля  
/interests - Управление интересами
/reminder - Настройка напоминаний"""
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=get_main_keyboard()
                )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка при регистрации. Попробуйте позже."
        )


async def show_interests_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, db_user) -> None:
    """Show interests selection interface."""
    from messages import format_available_interests
    message_text = "🎯 **Выбор интересов**\n\n"
    message_text += format_available_interests()
    message_text += "\n\n💡 **Инструкция:**\nОтправьте команду с номерами интересов через запятую.\nПример: `/interests 1,3,5`"
    
    await update.message.reply_text(
        message_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """📖 **Справка по командам**

**Основные команды:**

/start - Начать работу с ботом
Зарегистрирует вас в системе и покажет приветственное сообщение

/help - Показать эту справку
Отображает список всех доступных команд

/config - Показать настройки профиля
Показывает ваши данные и выбранные интересы

/interests - Управление интересами
Позволяет выбрать или изменить ваши интересы

/reminder - Настройка напоминаний
Настрой интервал напоминаний о прогрессе (1-7 дней)

**Как использовать:**

1. Начните с команды /start для регистрации
2. Используйте /interests для выбора ваших интересов
3. Настройте напоминания через /reminder
4. Просматривайте свой профиль через /config

**Примеры:**

Выбор интересов:
`/interests 1,3,5`

Настройка напоминаний:
`/reminder 3` - напоминать каждые 3 дня

**О напоминаниях:**

Бот будет автоматически напоминать тебе о твоем прогрессе. Когда придет напоминание, просто ответь на вопросы:
- Что ты изучал?
- Сколько времени потратил?

Бот сохранит твой прогресс и подбодрит тебя! 💪

Также используйте кнопки ниже для быстрого доступа! 👇"""
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user configuration and information."""
    error_msg, config_text = await get_user_config_text(update.message.from_user.id)
    if error_msg:
        await update.message.reply_text(
            error_msg,
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            config_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )


async def get_user_config_text(user_id: int) -> tuple[str | None, str]:
    """Get user configuration text. Returns (error_message, config_text)."""
    db_user = await get_user_by_telegram_id(user_id)
    if not db_user:
        return "Пожалуйста, сначала используйте команду /start", ""
    
    interests = await get_user_interests(db_user.id)
    config_text = format_user_config(db_user, interests)
    return None, config_text


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        help_text = """📖 **Справка по командам**

**Основные команды:**

/start - Начать работу с ботом
Зарегистрирует вас в системе и покажет приветственное сообщение

/help - Показать эту справку
Отображает список всех доступных команд

/config - Показать настройки профиля
Показывает ваши данные и выбранные интересы

/interests - Управление интересами
Позволяет выбрать или изменить ваши интересы

/reminder - Настройка напоминаний
Настрой интервал напоминаний о прогрессе (1-7 дней)

**Как использовать:**

1. Начните с команды /start для регистрации
2. Используйте /interests для выбора ваших интересов
3. Настройте напоминания через /reminder
4. Просматривайте свой профиль через /config

**Примеры:**

Выбор интересов:
`/interests 1,3,5`

Настройка напоминаний:
`/reminder 3` - напоминать каждые 3 дня

**О напоминаниях:**

Бот будет автоматически напоминать тебе о твоем прогрессе. Когда придет напоминание, просто ответь на вопросы:
- Что ты изучал?
- Сколько времени потратил?

Бот сохранит твой прогресс и подбодрит тебя! 💪

Также используйте кнопки ниже для быстрого доступа! 👇"""
        await query.edit_message_text(
            text=help_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    elif query.data == "config":
        error_msg, config_text = await get_user_config_text(query.from_user.id)
        if error_msg:
            await query.edit_message_text(
                text=error_msg,
                reply_markup=get_main_keyboard()
            )
        else:
            await query.edit_message_text(
                text=config_text,
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
            )


async def users_interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /interests is issued."""
    user = update.message.from_user
    
    try:
        # Get user from database
        db_user = await get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text(
                "Пожалуйста, сначала используйте команду /start для регистрации",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Check if user provided interests as command arguments (backward compatibility)
        if context.args:
            # Parse selected interests from command arguments
            await process_interests_input(user.id, ' '.join(context.args), db_user, update)
            return
        
        # Asking user to select their interests - set waiting state
        current_interests = await get_user_interests(db_user.id)
        
        message_text = "🎯 **Выбор интересов**\n\n"
        if current_interests:
            message_text += f"Текущие интересы:\n{format_interests_list(current_interests)}\n"
            message_text += "─" * 20 + "\n\n"
        
        message_text += format_available_interests()
        message_text += "\n\n💡 **Инструкция:**\nОтправьте номера интересов через запятую в следующем сообщении.\n**Пример:** `1,3,5`"
        
        # Set user as waiting for interests input
        user_waiting_for_interests[user.id] = True
        
        await update.message.reply_text(
            message_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
            
    except Exception as e:
        logger.error(f"Error in users_interests command: {e}", exc_info=True)
        if user.id in user_waiting_for_interests:
            del user_waiting_for_interests[user.id]
        await update.message.reply_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )


async def process_interests_input(user_id: int, interests_str: str, db_user, update: Update) -> None:
    """Process interests input from user."""
    try:
        # Parse selected interests
        selected_indices = [int(arg.strip()) for arg in interests_str.split(',') if arg.strip()]
        
        # Validate indices
        valid_indices = [i for i in selected_indices if 1 <= i <= len(INTERESTS_LIST)]
        invalid_indices = [i for i in selected_indices if i not in valid_indices]
        
        if invalid_indices:
            await update.message.reply_text(
                f"⚠️ Некорректные номера: {', '.join(map(str, invalid_indices))}\n"
                f"Пожалуйста, используйте номера от 1 до {len(INTERESTS_LIST)}\n\n"
                f"Попробуйте еще раз или используйте /interests для отмены."
            )
            return
        
        selected_interests = [INTERESTS_LIST[i-1] for i in valid_indices]
        
        if selected_interests:
            # Saving user interests to database
            logger.info(f"Saving interests for user {db_user.id}: {selected_interests}")
            success = await save_user_interests(db_user.id, selected_interests)
            
            if success:
                # Verify that interests were saved
                saved_interests = await get_user_interests(db_user.id)
                logger.info(f"Interests saved. Retrieved from DB: {saved_interests}")
                
                if saved_interests:
                    # Clear waiting state
                    if user_id in user_waiting_for_interests:
                        del user_waiting_for_interests[user_id]
                    
                    await update.message.reply_text(
                        "✅ Ваши интересы успешно сохранены!",
                        reply_markup=get_main_keyboard()
                    )
                    await update.message.reply_text(format_interests_list(saved_interests))
                else:
                    await update.message.reply_text(
                        "⚠️ Произошла ошибка при сохранении. Попробуйте еще раз.\n"
                        "Используйте /interests для повторной попытки."
                    )
            else:
                await update.message.reply_text(
                    "❌ Ошибка при сохранении интересов. Попробуйте позже.\n"
                    "Используйте /interests для повторной попытки."
                )
        else:
            await update.message.reply_text(
                "Некорректные номера интересов. Попробуйте снова.\n"
                "Используйте /interests для отмены."
            )
    except ValueError as e:
        logger.error(f"Error parsing interests: {e}")
        await update.message.reply_text(
            "❌ Неверный формат. Пожалуйста, отправьте номера через запятую.\n"
            "**Пример:** `1,3,5`\n\n"
            "Используйте /interests для отмены."
        )


# Reminder system
async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Setup reminder settings."""
    user = update.message.from_user
    
    try:
        db_user = await get_user_by_telegram_id(user.id)
        if not db_user:
            await update.message.reply_text(
                "Пожалуйста, сначала используйте команду /start для регистрации",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Check if user provided interval as command argument (backward compatibility)
        if context.args:
            try:
                interval_days = int(context.args[0])
                await process_reminder_interval(user.id, interval_days, db_user, update)
                return
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат. Используйте число от 1 до 7."
                )
                return
        
        # Show current settings and ask for new interval
        reminder = await get_user_reminder(db_user.id)
        if reminder:
            status = "включены" if reminder.is_enabled else "выключены"
            next_date = reminder.next_reminder_date.strftime("%d.%m.%Y %H:%M") if reminder.next_reminder_date else "не установлено"
            text = f"""⏰ **Настройки напоминаний**

Статус: {status}
Интервал: каждые {reminder.reminder_interval_days} дн{'я' if reminder.reminder_interval_days in [2, 3, 4] else 'ень' if reminder.reminder_interval_days == 1 else 'ей'}
Следующее напоминание: {next_date}

Чтобы изменить интервал, отправьте число от 1 до 7 в следующем сообщении.
**Пример:** `3` (каждые 3 дня)"""
        else:
            text = """⏰ **Настройка напоминаний**

Я могу напоминать тебе о твоем прогрессе в изучении!

Выбери интервал напоминаний (от 1 до 7 дней):
`1` - каждый день
`3` - каждые 3 дня
`7` - раз в неделю

Отправьте число в следующем сообщении.
**Пример:** `3`"""
        
        # Set user as waiting for reminder interval input
        user_waiting_for_reminder_interval[user.id] = True
        
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
    
    except Exception as e:
        logger.error(f"Error in reminder_command: {e}", exc_info=True)
        if user.id in user_waiting_for_reminder_interval:
            del user_waiting_for_reminder_interval[user.id]
        await update.message.reply_text("❌ Произошла ошибка.")


async def process_reminder_interval(user_id: int, interval_days: int, db_user, update: Update) -> None:
    """Process reminder interval input from user."""
    try:
        if interval_days < 1 or interval_days > 7:
            await update.message.reply_text(
                "⚠️ Интервал должен быть от 1 до 7 дней.\n"
                "Попробуйте еще раз или используйте /reminder для отмены."
            )
            return
        
        success = await create_or_update_reminder(db_user.id, interval_days)
        if success:
            # Clear waiting state
            if user_id in user_waiting_for_reminder_interval:
                del user_waiting_for_reminder_interval[user_id]
            
            await update.message.reply_text(
                f"✅ Напоминания настроены!\n"
                f"Я буду напоминать тебе каждые {interval_days} дн{'я' if interval_days in [2, 3, 4] else 'ень' if interval_days == 1 else 'ей'}\n\n"
                f"Следующее напоминание: через {interval_days} дн{'я' if interval_days in [2, 3, 4] else 'ень' if interval_days == 1 else 'ей'}",
                reply_markup=get_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка при сохранении настроек.\n"
                "Попробуйте еще раз или используйте /reminder для отмены."
            )
    except Exception as e:
        logger.error(f"Error processing reminder interval: {e}", exc_info=True)
        if user_id in user_waiting_for_reminder_interval:
            del user_waiting_for_reminder_interval[user_id]
        await update.message.reply_text("❌ Произошла ошибка.")


# Handler for reminder responses
user_waiting_for_progress = {}  # {user_id: {'waiting_for': 'topic' or 'time', 'topic': ...}}

# Handler for interests selection
user_waiting_for_interests = {}  # {user_id: True} - user is waiting to enter interests

# Handler for reminder interval selection
user_waiting_for_reminder_interval = {}  # {user_id: True} - user is waiting to enter reminder interval


async def handle_progress_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user responses to reminder questions and interests input."""
    user = update.message.from_user
    user_id = user.id
    
    # Check if user is waiting for reminder interval input
    if user_id in user_waiting_for_reminder_interval:
        try:
            db_user = await get_user_by_telegram_id(user_id)
            if not db_user:
                if user_id in user_waiting_for_reminder_interval:
                    del user_waiting_for_reminder_interval[user_id]
                return
            
            interval_str = update.message.text.strip()
            try:
                interval_days = int(interval_str)
                await process_reminder_interval(user_id, interval_days, db_user, update)
            except ValueError:
                await update.message.reply_text(
                    "❌ Неверный формат. Пожалуйста, отправьте число от 1 до 7.\n"
                    "**Пример:** `3`\n\n"
                    "Используйте /reminder для отмены."
                )
            return
        except Exception as e:
            logger.error(f"Error handling reminder interval input: {e}", exc_info=True)
            if user_id in user_waiting_for_reminder_interval:
                del user_waiting_for_reminder_interval[user_id]
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке. Попробуйте /reminder еще раз."
            )
            return
    
    # Check if user is waiting for interests input
    if user_id in user_waiting_for_interests:
        try:
            db_user = await get_user_by_telegram_id(user_id)
            if not db_user:
                if user_id in user_waiting_for_interests:
                    del user_waiting_for_interests[user_id]
                return
            
            interests_str = update.message.text.strip()
            await process_interests_input(user_id, interests_str, db_user, update)
            return
        except Exception as e:
            logger.error(f"Error handling interests input: {e}", exc_info=True)
            if user_id in user_waiting_for_interests:
                del user_waiting_for_interests[user_id]
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке. Попробуйте /interests еще раз."
            )
            return
    
    # Check if user is waiting for progress reminder
    if user_id not in user_waiting_for_progress:
        return
    
    try:
        db_user = await get_user_by_telegram_id(user_id)
        if not db_user:
            return
        
        state = user_waiting_for_progress[user_id]
        
        if state.get('waiting_for') == 'topic':
            # User provided topic
            topic = update.message.text.strip()
            if len(topic) > 200:
                await update.message.reply_text("Тема слишком длинная. Пожалуйста, укажи короче (до 200 символов).")
                return
            
            user_waiting_for_progress[user_id] = {
                'waiting_for': 'time',
                'topic': topic
            }
            await update.message.reply_text(
                f"Отлично! Ты изучал: {topic}\n\n"
                "⏱ Сколько времени ты потратил? (в минутах)\n"
                "Например: 30, 60, 120"
            )
        
        elif state.get('waiting_for') == 'time':
            # User provided time
            try:
                time_minutes = int(update.message.text.strip())
                if time_minutes <= 0:
                    await update.message.reply_text("Время должно быть положительным числом. Попробуй еще раз.")
                    return
                if time_minutes > 1440:  # 24 hours
                    await update.message.reply_text("Это слишком много! Максимум 1440 минут (24 часа). Попробуй еще раз.")
                    return
                
                topic = state.get('topic', 'Не указано')
                
                # Save progress
                success = await save_study_progress(user_id, topic, time_minutes)
                
                if success:
                    # Get stats
                    stats = await get_user_study_stats(user_id)
                    total_hours = stats['total_time_minutes'] // 60
                    total_minutes = stats['total_time_minutes'] % 60
                    
                    # Motivational messages
                    motivational_msgs = [
                        "🎉 Отличная работа! Продолжай в том же духе!",
                        "💪 Ты делаешь прогресс! Каждый день приближает тебя к цели!",
                        "🌟 Превосходно! Не останавливайся!",
                        "🚀 Ты на правильном пути! У тебя все получается!",
                        "✨ Замечательно! Твои усилия не напрасны!",
                    ]
                    
                    import random
                    motivational = random.choice(motivational_msgs)
                    
                    message = f"{motivational}\n\n"
                    message += "📊 **Твоя статистика:**\n"
                    message += f"Тем изучено: {stats['total_topics']}\n"
                    message += f"Общее время: {total_hours} ч {total_minutes} мин\n\n"
                    message += f"Сегодня ты добавил: {time_minutes} мин изучения по теме '{topic}'"
                    
                    await update.message.reply_text(message, parse_mode='Markdown')
                    
                    # Update reminder date
                    reminder = await get_user_reminder(user_id)
                    if reminder:
                        next_date = datetime.utcnow() + timedelta(days=reminder.reminder_interval_days)
                        await update_reminder_date(user_id, next_date)
                    
                    # Clear waiting state
                    del user_waiting_for_progress[user_id]
                else:
                    await update.message.reply_text("❌ Ошибка при сохранении. Попробуй еще раз.")
                    del user_waiting_for_progress[user_id]
            
            except ValueError:
                await update.message.reply_text("Пожалуйста, укажи число (в минутах). Например: 30, 60, 120")
    
    except Exception as e:
        logger.error(f"Error handling progress response: {e}", exc_info=True)
        if user_id in user_waiting_for_progress:
            del user_waiting_for_progress[user_id]
        await update.message.reply_text("❌ Произошла ошибка.")


async def send_reminder_to_user(user_id: int, application: Application) -> None:
    """Send reminder to a specific user."""
    try:
        reminder = await get_user_reminder(user_id)
        if not reminder or not reminder.is_enabled:
            return
        
        db_user = await get_user_by_telegram_id(user_id)
        if not db_user:
            return
        
        # Set user as waiting for progress
        user_waiting_for_progress[user_id] = {'waiting_for': 'topic'}
        
        message = f"👋 Привет, {db_user.first_name or 'друг'}!\n\n"
        message += "⏰ Время подвести итоги!\n\n"
        message += "📚 Что ты изучал с последнего напоминания?\n"
        message += "Напиши тему или предмет, который ты изучал."
        
        await application.bot.send_message(
            chat_id=user_id,
            text=message
        )
        
        logger.info(f"Reminder sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending reminder to user {user_id}: {e}", exc_info=True)
        if user_id in user_waiting_for_progress:
            del user_waiting_for_progress[user_id]


async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Background task to check and send reminders."""
    try:
        users_due = await get_users_due_for_reminder()
        for reminder in users_due:
            await send_reminder_to_user(reminder.user_id, context.application)
    except Exception as e:
        logger.error(f"Error in check_reminders: {e}", exc_info=True)


def main() -> None:
    """Start the bot."""
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Error: Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Initialize database
    asyncio.run(init_db())
    logger.info("Database initialized")
    
    # Define post_init handler for background tasks (must be defined before Application creation)
    async def post_init_handler(app: Application) -> None:
        """Run after application initialization - start reminder checker task."""
        async def reminder_checker_task():
            """Background task to check reminders periodically."""
            await asyncio.sleep(60)  # Wait 1 minute after start
            while True:
                try:
                    # Get all users due for reminders
                    users_due = await get_users_due_for_reminder()
                    for reminder in users_due:
                        await send_reminder_to_user(reminder.user_id, app)
                    # Check every hour
                    await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    logger.info("Reminder checker task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in reminder checker task: {e}", exc_info=True)
                    await asyncio.sleep(3600)  # Wait before retrying
        
        # Start the background task
        asyncio.create_task(reminder_checker_task())
        logger.info("Reminder checker task started")
    
    # Create the Application with post_init callback
    application = Application.builder().token(token).post_init(post_init_handler).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("interests", users_interests))
    application.add_handler(CommandHandler("reminder", reminder_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    # Handler for reminder responses (must be after command handlers)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_progress_response))
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

