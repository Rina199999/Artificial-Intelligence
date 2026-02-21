from datetime import datetime

def log_message(user_input, response):
    with open("chat_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] USER: {user_input}\n")
        f.write(f"[{datetime.now()}] BOT: {response}\n")