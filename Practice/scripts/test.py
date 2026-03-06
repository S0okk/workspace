import asyncio

import requests


def blocking_get_data():
    # Эта функция блокирует поток на время сетевого запроса
    response = requests.get("https://example.com")
    return response.status_code


async def main():
    print("Запускаю блокирующую задачу...")

    # Запускаем в отдельном потоке и ждем результат асинхронно
    result = await asyncio.to_thread(blocking_get_data)

    print(f"Готово! Результат: {result}")


asyncio.run(main())
