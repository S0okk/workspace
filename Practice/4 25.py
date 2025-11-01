import time

class Notification:
    def __init__(self, user_id, message, send_at):
        self.user_id = user_id
        self.message = message
        self.send_at = send_at
        self.id = 1
        self.notification_dict = {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'send_at': self.send_at
            }
    
    def __repr__(self) -> str:
        return f"id: {self.id}, user_id: {self.user_id}, message: {self.message}, send_at: {self.send_at}"

class Scheduler:
    def __init__(self):
        self.notifications = []
    
    def schedule(self, notification):
        self.notifications.append(notification.notification_dict)
    
    def run_pending(self) -> list:
        return self.notifications
    
    def send_notification(self) -> list:
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        must_be_sended = [notification for notification in self.notifications if notification['send_at'] <= current_time]
        return must_be_sended

notification = Notification(user_id='254', message='Hello beginner', send_at='2024-10-25 21:48:39')
schedule_254 = Scheduler()
schedule_254.schedule(notification)
print(schedule_254.send_notification())

new_feature = 'text'