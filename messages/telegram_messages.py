import os, requests
from typing import override
from datetime import datetime
from dotenv import load_dotenv
from .message import Message

load_dotenv(dotenv_path="../.env")

SCOPES = os.getenv("SCOPES")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
BASE_URL_SEND = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text="
URL_GET_MESSAGE = f"https://api.telegram.org/bot{TOKEN}/getUpdates"


class TelegramMessage(Message):
    """
    Receive and send message(s) related to Telegram
    """
    def __init__(self, initial_timestamp):
        self.last_time_checked = initial_timestamp

    @override
    def send_message(self, message):
        url_send = BASE_URL_SEND + message + "&amp;parse_mode=MarkdownV2"
        response = requests.get(url_send).json()
        if not response["ok"]:
            raise ValueError("Failed to send message")
        return "Message successfully sent on Telegram"

    @override
    def get_new_message(self):
        response = requests.get(URL_GET_MESSAGE).json()
        new_message = ""
        if not response["result"]:
            return new_message
    
        update = response["result"][-1]
        message = update['message']
        if message["date"] > self.last_time_checked:
            new_message = (f"Message: { message['text'] }\n"
                            f"Current date/time: { datetime.fromtimestamp(message["date"]).strftime("%Y-%m-%d %H:%M") }"
                          )
            self.last_time_checked = message["date"]
        return new_message