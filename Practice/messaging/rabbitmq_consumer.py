"""RabbitMQ consumer module with CLI and safe connection handling.

Usage:
  python rabbitmq_consumer.py --host localhost --port 5672 --queue hello
"""

import argparse
import logging
import sys
from typing import Optional

import pika


def make_connection(
    host: str, port: int, vhost: str, username: str, password: str
) -> pika.BlockingConnection:
    params = pika.ConnectionParameters(
        host=host,
        port=port,
        virtual_host=vhost,
        credentials=pika.PlainCredentials(username=username, password=password),
    )
    return pika.BlockingConnection(params)


def callback(ch, method, properties, body):
    try:
        text = body.decode() if isinstance(body, (bytes, bytearray)) else str(body)
    except Exception:
        text = repr(body)
    logging.info("Received: %s", text)


def run_consumer(
    host: str, port: int, vhost: str, username: str, password: str, queue: str
) -> None:
    connection: Optional[pika.BlockingConnection] = None
    try:
        connection = make_connection(host, port, vhost, username, password)
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)
        logging.info("Waiting for messages on queue '%s'...", queue)
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down")
    except Exception as exc:
        logging.exception("Consumer error: %s", exc)
    finally:
        if connection is not None and getattr(connection, "is_closed", True) is False:
            try:
                connection.close()
            except Exception:
                pass


def parse_args(argv):
    p = argparse.ArgumentParser(description="RabbitMQ consumer")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=5672)
    p.add_argument("--vhost", default="/")
    p.add_argument("--username", default="admin")
    p.add_argument("--password", default="admin")
    p.add_argument("--queue", default="hello")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    run_consumer(
        args.host, args.port, args.vhost, args.username, args.password, args.queue
    )


if __name__ == "__main__":
    main()
