import asyncio
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Optional, Tuple

from database import (
    complete_reminder_and_optional_daily,
    create_or_update_reminder,
    create_user,
    get_all_dailies,
    get_daily_to_answer,
    get_or_create_daily,
    get_or_create_streak,
    get_user_by_telegram_id,
    get_user_interests,
    get_user_reminder,
    get_user_streak_info,
    get_user_study_stats,
    get_users_due_for_reminder,
    init_db,
    initialize_default_dailies,
    prepare_reminder_for_user,
    save_study_progress,
    save_user_interests,
    update_reminder_date,
    update_streak,
)
from dotenv import load_dotenv
from messages import (
    DAILY_QUESTIONS,
    INTERESTS_LIST,
    format_available_interests,
    format_daily_message,
    format_interests_list,
    format_streak_message,
)
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

# Configure logging
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    format=log_format,
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Constants
MIN_REMINDER_DAYS = 1
MAX_REMINDER_DAYS = 7
DAILY_REPEAT_INTERVAL = 3
MAX_MESSAGE_LENGTH = 4096

# User state tracking
user_states = {}  # {user_id: {'state': 'interests'|'reminder'|'daily', 'data': {...}}}


def get_main_keyboard():
    """Create main keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📖 Помощь", callback_data="help"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="config"),
        ],
        [
            InlineKeyboardButton("🔥 Мой стрик", callback_data="streak"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def format_user_config(db_user, interests: list[str]) -> str:
    """Format user configuration information."""
    config_text = "⚙️ **Ваши настройки:**\n\n"
    config_text += f"**ID пользователя:** {db_user.id}\n"
    config_text += f"**Telegram ID:** {db_user.telegram_id}\n"
    config_text += f"**Имя:** {db_user.first_name or 'Не указано'}\n"
    config_text += f"**Фамилия:** {db_user.last_name or 'Не указано'}\n"
    config_text += (
        f"**Username:** @{db_user.username if db_user.username else 'Не указано'}\n"
    )
    config_text += (
        f"**Статус:** {'Активен ✅' if db_user.is_active else 'Неактивен ❌'}\n\n"
    )

    config_text += "**Ваши интересы:**\n"
    if interests:
        for i, interest in enumerate(interests, 1):
            config_text += f"{i}. {interest}\n"
    else:
        config_text += "Интересы не выбраны. Используйте /interests для выбора.\n"

    return config_text


async def safe_edit_message(query, text: str, parse_mode: str = "Markdown") -> bool:
    """Safely edit message with error handling."""
    try:
        await query.edit_message_text(
            text=text[:MAX_MESSAGE_LENGTH],
            parse_mode=parse_mode,
            reply_markup=get_main_keyboard(),
        )
        return True
    except TelegramError as e:
        logger.warning(f"Failed to edit message: {e}")
        return False


async def safe_reply_message(
    update: Update, text: str, parse_mode: str = "Markdown"
) -> bool:
    """Safely send reply message with error handling."""
    try:
        await update.message.reply_text(
            text=text[:MAX_MESSAGE_LENGTH],
            parse_mode=parse_mode,
            reply_markup=get_main_keyboard(),
        )
        return True
    except TelegramError as e:
        logger.warning(f"Failed to send message: {e}")
        return False


async def ensure_user_exists(user) -> Optional[object]:
    """Ensure user exists in database."""
    try:
        db_user = await get_user_by_telegram_id(user.id)
        if not db_user:
            db_user = await create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            await get_or_create_streak(db_user.id)
            logger.info(f"New user: {user.id} (@{user.username})")
        return db_user
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}", exc_info=True)
        return None


async def get_user_config_text(user_id: int) -> Tuple[Optional[str], str]:
    """Get user configuration text."""
    try:
        db_user = await get_user_by_telegram_id(user_id)
        if not db_user:
            return "Используйте /start для регистрации", ""

        interests = await get_user_interests(db_user.id)
        config_text = format_user_config(db_user, interests)
        return None, config_text
    except Exception as e:
        logger.error(f"Error getting user config: {e}", exc_info=True)
        return "Ошибка при загрузке конфига", ""


# ==================== COMMAND HANDLERS ====================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user = update.message.from_user

    try:
        db_user = await ensure_user_exists(user)
        if not db_user:
            await safe_reply_message(update, "❌ Ошибка при регистрации.")
            return

        interests = await get_user_interests(db_user.id)

        welcome_text = f"""🎉 Добро пожаловать, {user.first_name or 'друг'}!

Я дейлик бот - помогу тебе:
• Отвечать на интересные вопросы каждый день
• Отслеживать свой прогресс
• Сохранять день-стрик 🔥

{'**Выбери свои интересы!**' if not interests else 'Ты готов(а) начать? 👇'}"""
        # Add a short hint for the user-friendly flow
        welcome_text += "\n\nНажми «Начать настройку», чтобы быстро выбрать интервал напоминаний и интересы."

        # Send one message with action buttons to drive initial setup
        welcome_keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🚀 Начать настройку", callback_data="begin_setup"
                    )
                ],
                [InlineKeyboardButton("➡️ Пропустить", callback_data="skip_setup")],
            ]
        )

        # Show greeting with a persistent "Начать настройку" button.
        # Setup will only start when the user presses the button.
        msg = await update.message.reply_text(
            welcome_text, parse_mode="Markdown", reply_markup=welcome_keyboard
        )

    except Exception as e:
        logger.error(f"Error in start: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка при регистрации.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    help_text = """📖 **Справка по командам**

**/daily** - Ответить на дневное задание
**/streak** - Посмотреть свой стрик 🔥
**/interests** - Управление интересами
**/reminder** - Настройка напоминаний о прогрессе
**/config** - Настройки профиля

**Как это работает:**
1. Выбери интересы (/interests)
2. Отвечай на ежедневные дейлики (/daily)
3. Следи за своим стриком (/streak)

**День-стрик:**
Отвечай на дейлики каждый день и сохраняй свой стрик! 🔥🔥🔥"""

    await safe_reply_message(update, help_text)


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user configuration."""
    error_msg, config_text = await get_user_config_text(update.message.from_user.id)
    if error_msg:
        await safe_reply_message(update, error_msg)
    else:
        await safe_reply_message(update, config_text)


async def users_interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /interests command."""
    user = update.message.from_user

    try:
        db_user = await ensure_user_exists(user)
        if not db_user:
            await safe_reply_message(update, "❌ Используйте /start для регистрации.")
            return

        if context.args:
            await process_interests_input(
                user.id, " ".join(context.args), db_user, update
            )
            return

        current_interests = await get_user_interests(db_user.id)

        message_text = "🎯 **Выбор интересов**\n\n"
        if current_interests:
            message_text += f"Текущие интересы:\n{format_interests_list(current_interests)}\n─────\n\n"

        message_text += format_available_interests()
        message_text += "\n\nОтправьте номера через запятую (пример: `1,3,5`)"

        user_states[user.id] = {"state": "interests", "db_user": db_user}
        await safe_reply_message(update, message_text)

    except Exception as e:
        logger.error(f"Error in users_interests: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка.")


async def process_interests_input(
    user_id: int, interests_str: str, db_user, update: Update
) -> None:
    """Process interests input from user."""
    try:
        selected_indices = []
        for arg in interests_str.split(","):
            try:
                idx = int(arg.strip())
                selected_indices.append(idx)
            except ValueError:
                pass

        valid_indices = [i for i in selected_indices if 1 <= i <= len(INTERESTS_LIST)]
        invalid_indices = [i for i in selected_indices if i not in valid_indices]

        if invalid_indices or not selected_indices:
            await safe_reply_message(
                update,
                f"⚠️ Некорректные номера. Используйте от 1 до {len(INTERESTS_LIST)}\nПример: `1,3,5`",
            )
            return

        selected_interests = list(set([INTERESTS_LIST[i - 1] for i in valid_indices]))
        success = await save_user_interests(db_user.id, selected_interests)

        if success:
            response = f"✅ Интересы сохранены!\n\n"
            for interest in selected_interests:
                response += f"• {interest}\n"

            # If we are in initial setup flow and were asked for interests, finish setup
            state_info = user_states.get(user_id)
            if (
                state_info
                and state_info.get("state") == "setup"
                and state_info.get("stage") == "interests"
            ):
                try:
                    chat_id = state_info.get("msg_chat_id")
                    msg_id = state_info.get("msg_id")
                    confirm_text = "✅ Настройка завершена!\n\nТы будешь получать дейлики по выбранному интервалу.\nОтветы засчитываются вместе с напоминанием."
                    token = os.getenv("TELEGRAM_BOT_TOKEN")
                    bot = Bot(token)
                    await bot.edit_message_text(
                        confirm_text,
                        chat_id=chat_id,
                        message_id=msg_id,
                        parse_mode="Markdown",
                        reply_markup=get_main_keyboard(),
                    )
                    if user_id in user_states:
                        del user_states[user_id]
                    return
                except Exception:
                    # fallback to sending a new message
                    response += "\n\nНастройка завершена!"

            response += f"\n\nИспользуй /reminder для настроек или дождись напоминания."
            await safe_reply_message(update, response)
            if user_id in user_states and user_states[user_id].get("state") != "setup":
                del user_states[user_id]
        else:
            await safe_reply_message(update, "❌ Ошибка при сохранении интересов.")

    except Exception as e:
        logger.error(f"Error processing interests: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка при обработке.")


async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reminder command."""
    user = update.message.from_user

    try:
        db_user = await ensure_user_exists(user)
        if not db_user:
            await safe_reply_message(update, "❌ Используйте /start для регистрации.")
            return

        if context.args:
            try:
                interval_days = int(context.args[0])
                await process_reminder_interval(user.id, interval_days, db_user, update)
                return
            except ValueError:
                pass

        reminder = await get_user_reminder(db_user.id)
        if reminder:
            status = "✅ включены" if reminder.is_enabled else "❌ выключены"
            next_date = (
                reminder.next_reminder_date.strftime("%d.%m %H:%M")
                if reminder.next_reminder_date
                else "не установлено"
            )
            text = f"""⏰ **Настройки напоминаний**

Статус: {status}
Интервал: каждые {reminder.reminder_interval_days} дн
Следующее: {next_date}

Отправьте число от 1 до 7 для изменения.
Пример: `3`"""
        else:
            text = f"""⏰ **Настройка напоминаний**

Я буду напоминать о твом прогрессе!

Выбери интервал (от {MIN_REMINDER_DAYS} до {MAX_REMINDER_DAYS} дней):
`1` - каждый день
`3` - каждые 3 дня
`7` - раз в неделю

Пример: `3`"""

        user_states[user.id] = {"state": "reminder", "db_user": db_user}
        await safe_reply_message(update, text)

    except Exception as e:
        logger.error(f"Error in reminder_command: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка.")


async def process_reminder_interval(
    user_id: int, interval_days: int, db_user, update: Update
) -> None:
    """Process reminder interval input."""
    try:
        if not (MIN_REMINDER_DAYS <= interval_days <= MAX_REMINDER_DAYS):
            await safe_reply_message(
                update,
                f"⚠️ Интервал должен быть от {MIN_REMINDER_DAYS} до {MAX_REMINDER_DAYS} дней.",
            )
            return

        success = await create_or_update_reminder(db_user.id, interval_days)
        if success:
            # If in setup flow, move to interests selection in the same editable message
            state_info = user_states.get(user_id)
            if (
                state_info
                and state_info.get("state") == "setup"
                and state_info.get("stage") == "reminder"
            ):
                chat_id = state_info.get("msg_chat_id")
                msg_id = state_info.get("msg_id")
                interests_text = (
                    "🎯 **Выбор интересов**\n\n" + format_available_interests()
                )
                interests_text += "\n\nОтправьте номера через запятую (пример: `1,3,5`)"
                logger.info(
                    f"User {user_id}: moving setup from reminder->interests, editing message {msg_id} in chat {chat_id}"
                )
                try:
                    token = os.getenv("TELEGRAM_BOT_TOKEN")
                    bot = Bot(token)
                    await bot.edit_message_text(
                        interests_text,
                        chat_id=chat_id,
                        message_id=msg_id,
                        parse_mode="Markdown",
                    )
                    # update state to interests stage
                    user_states[user_id] = {
                        "state": "setup",
                        "stage": "interests",
                        "db_user": db_user,
                        "msg_chat_id": chat_id,
                        "msg_id": msg_id,
                    }
                    return
                except Exception as exc:
                    logger.exception(
                        f"Failed to edit setup message for user {user_id}: {exc}"
                    )
                    # fallback: send interests as a new message and set state to interests
                    try:
                        await update.message.reply_text(
                            interests_text, parse_mode="Markdown"
                        )
                        user_states[user_id] = {
                            "state": "setup",
                            "stage": "interests",
                            "db_user": db_user,
                            "msg_chat_id": update.message.chat_id,
                            "msg_id": None,
                        }
                        return
                    except Exception as exc2:
                        logger.exception(
                            f"Fallback send interests failed for user {user_id}: {exc2}"
                        )

            if user_id in user_states:
                del user_states[user_id]

            await safe_reply_message(
                update,
                f"✅ Напоминания настроены!\nКаждые {interval_days} дн будут приходить уведомления.",
            )
        else:
            await safe_reply_message(update, "❌ Ошибка при сохранении настроек.")
    except Exception as e:
        logger.error(f"Error processing reminder: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка.")


# /daily command removed - daily flow is handled via reminders


async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /streak command."""
    user = update.message.from_user

    try:
        db_user = await ensure_user_exists(user)
        if not db_user:
            await safe_reply_message(update, "❌ Используйте /start для регистрации.")
            return

        streak_info = await get_user_streak_info(db_user.id)
        if not streak_info:
            await safe_reply_message(
                update, "📊 У тебя еще нет стрика. Ответь на первый дейлик!"
            )
            return

        message = format_streak_message(
            streak_info["current_streak"],
            streak_info["longest_streak"],
            streak_info["total_completed"],
        )
        await safe_reply_message(update, message)

    except Exception as e:
        logger.error(f"Error in streak_command: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка при загрузке стрика.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query

    try:
        await query.answer()

        if query.data == "help":
            help_text = """📖 **Справка**

/daily - Дейлик
/streak - Мой стрик 🔥
/interests - Интересы
/reminder - Напоминания
/config - Профиль

Отвечай на дейлики каждый день и сохраняй стрик!"""
            await safe_edit_message(query, help_text)

        elif query.data == "config":
            error_msg, config_text = await get_user_config_text(query.from_user.id)
            if error_msg:
                await safe_edit_message(query, error_msg)
            else:
                await safe_edit_message(query, config_text)

        elif query.data == "streak":
            db_user = await get_user_by_telegram_id(query.from_user.id)
            if not db_user:
                await safe_edit_message(query, "❌ Используйте /start для регистрации.")
                return

            streak_info = await get_user_streak_info(db_user.id)
            if not streak_info:
                await safe_edit_message(query, "📊 У тебя еще нет стрика.")
            else:
                message = format_streak_message(
                    streak_info["current_streak"],
                    streak_info["longest_streak"],
                    streak_info["total_completed"],
                )
                await safe_edit_message(query, message)

        # 'dailies' button removed — dailies are delivered only with reminders
        elif query.data == "begin_setup":
            # start full setup: ask for reminder interval first
            db_user = await get_user_by_telegram_id(query.from_user.id)
            if not db_user:
                await safe_edit_message(query, "❌ Используйте /start для регистрации.")
                return

            reminder_text = f"⏰ **Настройка напоминаний**\n\nВыбери интервал (от {MIN_REMINDER_DAYS} до {MAX_REMINDER_DAYS} дней):\n`1` - каждый день\n`3` - каждые 3 дня\n`7` - раз в неделю\n\nПример: `3`"
            try:
                await query.edit_message_text(reminder_text, parse_mode="Markdown")
                user_states[query.from_user.id] = {
                    "state": "setup",
                    "stage": "reminder",
                    "db_user": db_user,
                    "msg_chat_id": query.message.chat_id,
                    "msg_id": query.message.message_id,
                }
            except Exception:
                await safe_edit_message(query, reminder_text)

        elif query.data == "start_reminder":
            db_user = await get_user_by_telegram_id(query.from_user.id)
            if not db_user:
                await safe_edit_message(query, "❌ Используйте /start для регистрации.")
                return

            reminder_text = f"⏰ **Настройка напоминаний**\n\nВыбери интервал (от {MIN_REMINDER_DAYS} до {MAX_REMINDER_DAYS} дней):\n`1` - каждый день\n`3` - каждые 3 дня\n`7` - раз в неделю\n\nПример: `3`"
            try:
                await query.edit_message_text(reminder_text, parse_mode="Markdown")
                user_states[query.from_user.id] = {
                    "state": "setup",
                    "stage": "reminder",
                    "db_user": db_user,
                    "msg_chat_id": query.message.chat_id,
                    "msg_id": query.message.message_id,
                }
            except Exception:
                await safe_edit_message(query, reminder_text)

        elif query.data == "start_interests":
            db_user = await get_user_by_telegram_id(query.from_user.id)
            if not db_user:
                await safe_edit_message(query, "❌ Используйте /start для регистрации.")
                return

            setup_text = "🎯 **Выбор интересов**\n\n" + format_available_interests()
            setup_text += "\n\nОтправьте номера через запятую (пример: `1,3,5`)"
            try:
                await query.edit_message_text(setup_text, parse_mode="Markdown")
                user_states[query.from_user.id] = {
                    "state": "setup",
                    "stage": "interests",
                    "db_user": db_user,
                    "msg_chat_id": query.message.chat_id,
                    "msg_id": query.message.message_id,
                }
            except Exception:
                await safe_edit_message(query, setup_text)

        elif query.data == "skip_setup":
            try:
                await query.edit_message_text(
                    "✅ Хорошо — можно настроить позже. Используй /reminder или /interests.",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard(),
                )
                if query.from_user.id in user_states:
                    del user_states[query.from_user.id]
            except Exception:
                await safe_edit_message(
                    query,
                    "✅ Хорошо — можно настроить позже. Используй /reminder или /interests.",
                )

    except TelegramError as e:
        logger.error(f"Error in button_callback: {e}")


# ==================== MESSAGE HANDLERS ====================


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages for different states."""
    user = update.message.from_user
    user_id = user.id
    message_text = update.message.text.strip()

    if not message_text:
        return

    state_info = user_states.get(user_id)
    if not state_info:
        return

    try:
        # Support setup flow (single editable message with stages)
        if state_info.get("state") == "setup":
            stage = state_info.get("stage")
            if stage == "interests":
                await process_interests_input(
                    user_id, message_text, state_info["db_user"], update
                )
                return
            elif stage == "reminder":
                try:
                    interval_days = int(message_text)
                    await process_reminder_interval(
                        user_id, interval_days, state_info["db_user"], update
                    )
                except ValueError:
                    # try to edit the same message with error or fallback reply
                    await safe_reply_message(
                        update, "⚠️ Пожалуйста, введите число от 1 до 7."
                    )
                return

        if state_info.get("state") == "interests":
            await process_interests_input(
                user_id, message_text, state_info["db_user"], update
            )

        elif state_info.get("state") == "reminder":
            try:
                interval_days = int(message_text)
                await process_reminder_interval(
                    user_id, interval_days, state_info["db_user"], update
                )
            except ValueError:
                await safe_reply_message(
                    update, "⚠️ Пожалуйста, введите число от 1 до 7."
                )

        elif state_info.get("state") == "daily":
            db_user = state_info["db_user"]
            daily_id = state_info["daily_id"]

            # Use combined completion that updates reminder and saves answer
            success = await complete_reminder_and_optional_daily(
                db_user.id,
                daily_id=daily_id,
                answer=message_text,
                repeat_interval_days=DAILY_REPEAT_INTERVAL,
            )

            if success:
                # update_streak was already called inside complete_reminder...; fetch streak info
                streak_info = await get_user_streak_info(db_user.id)

                response = "✅ Спасибо за ответ!\n\n"
                if streak_info["current_streak"] > 0:
                    response += (
                        f"🔥 Твой стрик: **{streak_info['current_streak']} дней**\n"
                    )
                    if streak_info["current_streak"] % 5 == 0:
                        response += f"🎉 Миллион! Ты на огне!\n"
                else:
                    response += "📌 Ответ сохранён.\n"

                response += f"\nИспользуй /streak для статуса!"

                await safe_reply_message(update, response)
                if user_id in user_states:
                    del user_states[user_id]
            else:
                await safe_reply_message(update, "❌ Ошибка при сохранении ответа.")

    except Exception as e:
        logger.error(f"Error in handle_user_input: {e}", exc_info=True)
        await safe_reply_message(update, "❌ Ошибка. Попробуйте позже.")


# ==================== BACKGROUND TASKS ====================


async def send_reminder_to_user(user_id: int, application: Application) -> None:
    """Send reminder notification to user."""
    try:
        db_user = await get_user_by_telegram_id(user_id)
        if not db_user:
            return
        # Use integrated prepare function to fetch reminder and a daily (if due)
        prep = await prepare_reminder_for_user(user_id)
        if not prep:
            return
        reminder, daily = prep
        if not reminder or not reminder.is_enabled:
            return

        # If there's no daily to ask, still update reminder date and skip
        if not daily:
            await complete_reminder_and_optional_daily(user_id)
            logger.info(f"Reminder ticked (no daily) for user {user_id}")
            return

        message = f"⏰ Привет, {db_user.first_name or 'друг'}!\n\n"
        message += "🎯 Время для дейлика!\n\n"
        message += f"{daily.question}\n\n"
        message += "Используй /daily для ответа!"

        await application.bot.send_message(chat_id=user_id, text=message)

        # Update reminder date (and optionally handle daily answer later)
        await complete_reminder_and_optional_daily(user_id)

        logger.info(f"Reminder sent to user {user_id}")

    except TelegramError as e:
        logger.error(f"Error sending reminder to user {user_id}: {e}")


async def check_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Background task to check and send reminders."""
    try:
        users_due = await get_users_due_for_reminder()
        application = context.application

        for reminder in users_due:
            await send_reminder_to_user(reminder.user_id, application)
            await asyncio.sleep(0.1)

        if users_due:
            logger.info(f"Sent {len(users_due)} reminders")
    except Exception as e:
        logger.error(f"Error in check_reminders: {e}", exc_info=True)


# ==================== INITIALIZATION ====================


def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Error: Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return

    # Initialize everything in one async context
    async def async_init():
        await init_db()
        logger.info("Database initialized")
        await initialize_default_dailies()
        logger.info("Default dailies initialized")

    asyncio.run(async_init())

    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("interests", users_interests))
    application.add_handler(CommandHandler("reminder", reminder_command))
    # daily command removed; dailies are delivered with reminders
    application.add_handler(CommandHandler("streak", streak_command))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input)
    )

    # Add job queue for reminders
    application.job_queue.run_repeating(check_reminders, interval=300, first=10)

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
