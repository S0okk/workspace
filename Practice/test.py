import pika

class QueueProducer:
    def __init__(self, params):
        self.params = params
    
    def connect(self, queue_name):
        try:
            con_params = pika.ConnectionParameters(**self.params)
            con = pika.BlockingConnection(con_params)
            self.channel = con.channel()
            self.channel.queue_declare(queue=queue_name, durable=True)
        except Exception as e:
            print(f"Error: {e}")

    def send_message(self, queue_name, message):
        try:
            self.channel.basic_publish(exchange="", routing_key=queue_name, body=message)
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error: {e}")
    
    def close(self):
        try:
            self.channel.close()
        except Exception as e:
            print(f"Error: {e}")

prod = QueueProducer({
    "host": "localhost",
    "port": 5672,
    "virtual_host": "/",
    "credentials": pika.PlainCredentials(
        username="guest",
        password="guest",
    ),
})
prod.connect("hello")
prod.send_message("hello", "Hello, RabbitMQ!")
prod.close()