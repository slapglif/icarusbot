from dotenv import load_dotenv
import os

# Load .env file to set environment variables
load_dotenv()

# Load configuration values from environment variables

class Config:
    volume: str = os.environ.get("VOLUME")
    debug: str = os.environ.get("DEBUG")
    log_filename: str = os.environ.get("LOG_FILENAME")
    imap: str = os.environ.get("IMAP")
    user: str = os.environ.get("USER")
    pwd: str = os.environ.get("PWD")
    folder: str = os.environ.get("FOLDER", "[Gmail]/All Mail")
    stop_loss = os.environ.get("STOP_LOSS")
    take_profit = os.environ.get("TAKE_PROFIT")
    hedging: str = os.environ.get("HEDGE")
    bot_name: str = os.environ.get("BOT_NAME")
    socket1: str = os.environ.get("SOCKET1")
    socket2: str = os.environ.get("SOCKET2")
    target_symbol: str = os.environ.get("TARGET_SYMBOL")


