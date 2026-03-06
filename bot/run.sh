#!/bin/bash
# Скрипт для быстрого запуска бота

echo "🤖 Daily Bot - Telegram бот для дейликов"
echo ""

# Kill existing bot instances
echo "🛑 Завершение старых инстансов бота..."
pkill -f "python.*main.py" 2>/dev/null || true
sleep 1

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python не установлен. Пожалуйста, установите Python 3.8+"
    exit 1
fi

echo "✅ Python найден"
python3 --version

# Проверка виртуального окружения (используем единое окружение в корне workspace)
if [ ! -d "../.venv" ]; then
    echo ""
    echo "📦 Создание общего виртуального окружения в корне workspace..."
    python3 -m venv ../.venv
fi

# Активация виртуального окружения
echo ""
echo "🔌 Активация виртуального окружения..."
source ../.venv/bin/activate

# Установка зависимостей
echo ""
echo "📥 Установка зависимостей..."
pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  Файл .env не найден!"
    echo "Создание .env из примера..."
    cp .env.example .env
    echo ""
    echo "📝 Пожалуйста, отредактируйте .env файл и добавьте ваш TELEGRAM_BOT_TOKEN"
    echo "Получить токен можно у @BotFather в Telegram"
    exit 1
fi

# Проверка TELEGRAM_BOT_TOKEN
if ! grep -q "your_token_here" .env && grep -q "TELEGRAM_BOT_TOKEN=" .env; then
    echo "✅ .env файл настроен"
else
    echo "❌ TELEGRAM_BOT_TOKEN не установлен в .env файле"
    exit 1
fi

# Запуск бота
echo ""
echo "🚀 Запуск бота..."
python3 main.py
