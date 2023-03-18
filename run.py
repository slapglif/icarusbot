import imaplib

from app.bot.tv_mt4 import TradeHandler, EmailHandler, log

if __name__ == "__main__":
    log("Listening to email server...")

    trade_handler = TradeHandler()
    email_handler = EmailHandler(trade_handler)
    while True:
        try:
            email_handler.read_mail()
        except imaplib.IMAP4.error as _e:
            log(str(_e))
