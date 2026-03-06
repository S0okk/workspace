"""RabbitMQ producer module with CLI and safe connection handling."""

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


def send_message(
    host: str,
    port: int,
    vhost: str,
    username: str,
    password: str,
    queue: str,
    message: str,
) -> None:
    connection: Optional[pika.BlockingConnection] = None
    try:
        connection = make_connection(host, port, vhost, username, password)
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        channel.basic_publish(exchange="", routing_key=queue, body=message)
        logging.info("Sent message to queue '%s': %s", queue, message)
    except Exception:
        logging.exception("Producer error")
    finally:
        if connection is not None and getattr(connection, "is_closed", True) is False:
            try:
                connection.close()
            except Exception:
                pass


def parse_args(argv):
    p = argparse.ArgumentParser(description="RabbitMQ producer")
    p.add_argument("--host", default="localhost")
    p.add_argument("--port", type=int, default=5672)
    p.add_argument("--vhost", default="/")
    p.add_argument("--username", default="admin")
    p.add_argument("--password", default="admin")
    p.add_argument("--queue", default="hello")
    p.add_argument("--message", default="Hello, RabbitMQ!")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    send_message(
        args.host,
        args.port,
        args.vhost,
        args.username,
        args.password,
        args.queue,
        args.message,
    )


if __name__ == "__main__":
    main()
