# Welcome message
WELCOME_MESSAGE = """Привет! Я дейлик бот 🤖

Я помогу тебе найти единомышленников и интересные темы для обсуждения.

Используй команды:
/start - Начать работу с ботом
/help - Показать список команд
/config - Показать настройки профиля
/interests - Управление интересами
"""

# Help message
HELP_MESSAGE = """Я дейлик бот. Мои команды:

/start - Начать работу с ботом
/help - Показать эту справку
/config - Показать настройки профиля
/interests - Управление интересами

Также используйте кнопки ниже для быстрого доступа! 👇
"""

# Interests list
INTERESTS_LIST = [
    "Программирование",
    "Математика",
    "Физика",
    "Химия",
    "Биология",
    "История",
    "География",
    "Иностранные языки",
]


def format_interests_list(interests: list[str]) -> str:
    """Format interests list for display"""
    if not interests:
        return "У вас пока нет выбранных интересов."

    result = "Ваши интересы:\n"
    for i, interest in enumerate(interests, 1):
        result += f"{i}. {interest}\n"
    return result


def format_available_interests() -> str:
    """Format available interests for selection"""
    result = "Доступные интересы:\n"
    for i, interest in enumerate(INTERESTS_LIST, 1):
        result += f"{i}. {interest}\n"
    result += "\nОтправьте номера интересов через запятую (например: 1,3,5)"
    return result


# Sample daily questions by category
DAILY_QUESTIONS = {
    "general": [
        "Какую новую вещь ты выучил(а) сегодня?",
        "Что вдохновило тебя сегодня?",
        "Какую задачу ты решил(а) сегодня?",
        "Над чем ты работал(а) больше всего сегодня?",
    ],
    "Программирование": [
        "Какой алгоритм или структуру данных ты изучал(а)?",
        "Какой баг ты исправил(а) сегодня?",
        "Какой язык программирования ты практиковал(а)?",
        "На каком проекте ты работал(а)?",
    ],
    "Математика": [
        "Какую теорему или формулу ты выучил(а)?",
        "Какую задачу ты решил(а)?",
        "Какой раздел математики ты изучал(а)?",
    ],
    "Физика": [
        "Какой физический закон ты изучал(а)?",
        "Какой эксперимент ты провел(а)?",
        "Какое явление природы тебя удивило?",
    ],
}


def format_streak_message(
    current_streak: int, longest_streak: int, total_completed: int
) -> str:
    """Format streak information message"""
    fire = "🔥" * min(current_streak, 5)  # Max 5 fire emojis for visual
    return f"""🎯 **Твои достижения**

{fire} **Текущий стрик:** {current_streak} дней
⭐ **Лучший стрик:** {longest_streak} дней
📊 **Всего выполнено:** {total_completed} дейликов

{'💪 Отлично! Не теряй свой стрик!' if current_streak >= 3 else 'Начни новый стрик уже сегодня!'}"""


def format_daily_message(daily_question: str, repeat_count: int = 1) -> str:
    """Format daily question message"""
    repeat_info = (
        f"\n\n📌 Это уже {repeat_count}-й раз, когда мы возвращаемся к этому вопросу!"
        if repeat_count > 1
        else ""
    )
    return f"""📝 **Дневное задание**

{daily_question}{repeat_info}

Поделись своим ответом в следующем сообщении."""
