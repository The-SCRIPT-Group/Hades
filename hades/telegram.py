from urllib3 import PoolManager
from urllib3.exceptions import ProtocolError

# Initialize PoolManager
manager = PoolManager()


class TG:
    """
    Class to handle our telegram sending

    Has one attribute

    -> api_key: A Telegram bot API key

    Has various functions

    -> send: sends a message to the given `function` on the telegram API
    -> send_message: send(sendMessage)
    -> send_chat_action: send(sendChatAction)
    -> send_document: send(sendDocument)
    """

    def __init__(self, api_key):
        self.api_key = api_key

    def send(self, function, data):
        try:
            return manager.request(
                "POST",
                f"https://api.telegram.org/bot{self.api_key}/{function}",
                fields=data,
            )
        except ProtocolError as e:
            print(e, e.__class__)
            with open("extra-logs.txt", "a") as f:
                f.write(str(data) + "\n\n\n")

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

    def send_document(
        self,
        chat_id,
        caption,
        file_name,
        disable_notifications=False,
        parse_mode="HTML",
    ):
        data = {
            "caption": caption,
            "chat_id": chat_id,
            "document": (file_name, open(file_name, "rb").read()),
            "disable_notification": disable_notifications,
            "parse_mode": parse_mode,
        }
        return self.send("sendDocument", data)
