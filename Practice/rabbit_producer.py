import pika

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host='localhost', # Замените адрес на адрес вашего RabbitMQ сервера
    port=5672,        # Порт по умолчанию для RabbitMQ
    virtual_host='/', # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username='admin', # Имя пользователя по умолчанию
        password='admin'  # Пароль по умолчанию
    )
)

# Установка соединения
connection = pika.BlockingConnection(connection_params)

# Создание канала
channel = connection.channel()

# Имя очереди
queue_name = 'hello'

# Отправка сообщения
channel.queue_declare(queue=queue_name)  # Создание очереди (если не существует)

message = 'Hello, RabbitMQ!'
channel.basic_publish(
    exchange='',
    routing_key=queue_name,
    body=message
)

print(f"Sent: '{message}'")

# Закрытие соединения
connection.close()