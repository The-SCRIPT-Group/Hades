from urllib3 import PoolManager

manager = PoolManager()


class TG:
    def __init__(self, api_key):
        self.api_key = api_key

    def send(self, function, data):
        return manager.request(
            "POST",
            f"https://api.telegram.org/bot{self.api_key}/{function}",
            fields=data,
        )

    def send_message(self, chat_id, message, parse_mode="HTML"):
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        return self.send("sendMessage", data)

    def send_chat_action(self, chat_id, action):
        data = {
            "chat_id": chat_id,
            "action": action,
        }
        return self.send("sendChatAction", data)

    def send_document(self, chat_id, caption, file_name, disable_notifications=False):
        data = {
            "caption": caption,
            "chat_id": chat_id,
            "document": (file_name, open(file_name, "rb").read()),
            "disable_notification": disable_notifications,
        }
        return self.send("sendDocument", data)
