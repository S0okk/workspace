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

# Функция, которая будет вызвана при получении сообщения
def callback(ch, method, properties, body):
    print(f"Received: '{body}'")

# Подписка на очередь и установка обработчика сообщений
channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=True  # Автоматическое подтверждение обработки сообщений
)

print('Waiting for messages. To exit, press Ctrl+C')
channel.start_consuming()