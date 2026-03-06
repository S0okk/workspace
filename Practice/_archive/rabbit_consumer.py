import pika

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host="localhost",  # Замените адрес на адрес вашего RabbitMQ сервера
    port=5672,  # Порт по умолчанию для RabbitMQ
    virtual_host="/",  # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username="admin",  # Имя пользователя по умолчанию
        password="admin",  # Пароль по умолчанию
    ),
)


def callback(ch, method, properties, body):
    try:
        text = body.decode() if isinstance(body, (bytes, bytearray)) else str(body)
    except Exception:
        text = repr(body)
    print(f"Received: '{text}'")


def main():
    connection = None
    try:
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        queue_name = "hello"

        # Подписка на очередь и установка обработчика сообщений
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=True,  # Автоматическое подтверждение обработки сообщений
        )

        print("Waiting for messages. To exit, press Ctrl+C")
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Stopping...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if connection is not None and getattr(connection, "is_closed", True) is False:
            try:
                connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
