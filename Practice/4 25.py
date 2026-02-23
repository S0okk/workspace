import time
from datetime import datetime
import psycopg2

db_config = {
    'dbname': 'new_db',
    'user': 'postgres',
    'password': 'Yudacha30121981',
    'host': 'localhost',
    'port': '5432'
}


class Notification:
    def __init__(self, user_id, message, send_at):
        self.user_id = user_id
        self.message = message
        self.send_at = send_at

    def __repr__(self) -> str:
        return f"id: ?, user_id: {self.user_id}, message: {self.message}, send_at: {self.send_at}"


class Scheduler:
    def __init__(self, db_config=db_config):
        self.notifications = []
        self.db_config = db_config

    def schedule(self, notification: Notification):
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        sql = """ 
            INSERT INTO scheduled_notifications (user_id, message, send_at, status)
            VALUES (%s, %s, %s, %s)
        """
        cur.execute(sql, (notification.user_id, notification.message, notification.send_at, 'pending'))

        conn.commit()
        cur.close()
        conn.close()

    def run_pending(self) -> None:
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        now = datetime.now()

        cur.execute("""
            SELECT id, message, send_at
            FROM scheduled_notifications
            WHERE status = 'pending'
            AND send_at <= %s
        """, (now,))

        notifications = cur.fetchall()

        for notif in notifications:
            notif_id, message, send_at = notif
            print(f"🔔 Выполняется уведомление #{notif_id}: {message} (время {send_at})")

            cur.execute("""
                UPDATE scheduled_notifications
                SET status = 'sent'
                WHERE id = %s
            """, (notif_id,))

        conn.commit()
        cur.close()
        conn.close()

    def send_notification(self) -> list:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        must_be_sent = [
            n for n in self.notifications
            if n.send_at <= current_time
        ]
        return must_be_sent


# --- пример использования ---
notification = Notification(
    user_id='254',
    message='Hello beginner',
    send_at='2025-11-8 14:19:39'
)

scheduler = Scheduler()
scheduler.schedule(notification)
scheduler.run_pending()
print(scheduler.send_notification())
