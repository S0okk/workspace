import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from database import init_db, get_user_by_telegram_id, create_user, get_user_interests, save_user_interests
from messages import WELCOME_MESSAGE, HELP_MESSAGE, INTERESTS_LIST, format_interests_list, format_available_interests

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


async def format_user_config(db_user, interests: list[str]) -> str:
    """Format user configuration information."""
    config_text = "⚙️ **Ваши настройки:**\n\n"
    config_text += f"**ID пользователя:** {db_user.id}\n"
    config_text += f"**Telegram ID:** {db_user.telegram_id}\n"
    config_text += f"**Имя:** {db_user.first_name or 'Не указано'}\n"
    config_text += f"**Фамилия:** {db_user.last_name or 'Не указано'}\n"
    config_text += f"**Username:** @{db_user.username or 'Не указано'}\n"
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
    
    # Adding new user to database
    db_user = await get_user_by_telegram_id(user.id)
    if not db_user:
        await create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        logger.info(f"New user registered: {user.id} (@{user.username})")
    
    # Sending welcome message to user with buttons
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard()
    )
    
    # Sending list of commands to user
    await update.message.reply_text(HELP_MESSAGE)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        HELP_MESSAGE,
        reply_markup=get_main_keyboard()
    )


async def config_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user configuration and information."""
    user = update.message.from_user
    
    # Get user from database
    db_user = await get_user_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text(
            "Пожалуйста, сначала используйте команду /start",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Get user interests
    interests = await get_user_interests(db_user.id)
    
    # Format user information
    config_text = await format_user_config(db_user, interests)
    
    await update.message.reply_text(
        config_text,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await query.edit_message_text(
            text=HELP_MESSAGE,
            reply_markup=get_main_keyboard()
        )
    elif query.data == "config":
        user = query.from_user
        
        # Get user from database
        db_user = await get_user_by_telegram_id(user.id)
        if not db_user:
            await query.edit_message_text(
                text="Пожалуйста, сначала используйте команду /start",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Get user interests
        interests = await get_user_interests(db_user.id)
        
        # Format user information
        config_text = await format_user_config(db_user, interests)
        
        await query.edit_message_text(
            text=config_text,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )


async def users_interests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /interests is issued."""
    user = update.message.from_user
    
    # Get user from database
    db_user = await get_user_by_telegram_id(user.id)
    if not db_user:
        await update.message.reply_text("Пожалуйста, сначала используйте команду /start")
        return
    
    # Check if user is selecting interests (has text after command)
    if context.args:
        # Parse selected interests
        try:
            selected_indices = [int(arg.strip()) for arg in ''.join(context.args).split(',')]
            selected_interests = [INTERESTS_LIST[i-1] for i in selected_indices if 1 <= i <= len(INTERESTS_LIST)]
            
            if selected_interests:
                # Saving user interests to database
                await save_user_interests(db_user.id, selected_interests)
                await update.message.reply_text("Ваши интересы сохранены!")
                # Sending list of interests to user
                await update.message.reply_text(format_interests_list(selected_interests))
            else:
                await update.message.reply_text("Некорректные номера интересов. Попробуйте снова.")
        except (ValueError, IndexError):
            await update.message.reply_text("Пожалуйста, отправьте номера через запятую (например: /interests 1,3,5)")
    else:
        # Asking user to select their interests
        current_interests = await get_user_interests(db_user.id)
        if current_interests:
            await update.message.reply_text(format_interests_list(current_interests))
        await update.message.reply_text(format_available_interests())


def main() -> None:
    """Start the bot."""
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Error: Please set the TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Initialize database
    import asyncio
    asyncio.run(init_db())
    logger.info("Database initialized")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("config", config_command))
    application.add_handler(CommandHandler("interests", users_interests))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

