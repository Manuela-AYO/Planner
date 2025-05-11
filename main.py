import time
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from messages.telegram_messages import TelegramMessage
from personal_assistant.personal_assistant import PersonalAssistant

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

# model 
model = ChatGroq(model_name="deepseek-r1-distill-llama-70b", api_key=groq_api_key)

config = { "configurable": { "thread_id": "abc" } }
initial_timestamp = int(time.time())
tel_messages = TelegramMessage(initial_timestamp)
assistant = PersonalAssistant(model)

while True:
    # messages = tel_messages.get_new_telegram_messages()
    # if len(messages) > 0:
    #     for msg in messages:
    #         sent_message = (f"Message: { msg['text'] }\n"
    #                         f"Current date/time: { msg['date'] }"
    #                       )
    #         answer = manager.invoke(sent_message, config)
    #         tel_messages.send_telegram_message(answer)
    value = assistant.perform_task(tel_messages, config)
    if value:
        print(f"Message: {value}")
    else:
        print("...No message yet")
    time.sleep(5)