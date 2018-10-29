import email, imaplib
import random
import datetime, time
import logging
import json
from telegram.ext import (Updater, CommandHandler, RegexHandler, ConversationHandler)
import threading

SIGNALS = range(4)

db = Session()

with open('config.json') as json_data_file:
        config = json.load(json_data_file)


volume = config['volume']
debug = config['debug']
LOG_FILENAME = config['LOG_FILENAME']
STOPLOSS = config['STOPLOSS']
TAKEPROFIT = config['TAKEPROFIT']
token = config['token']
imap = config['imap']
user = config['user']
pwd = config['pwd']
folder = config['folder']



def log(msg):
    if debug == "1":
        print(msg)
    logging.info(msg)


# INIT
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)



def tele(direction, pair, bot, update):
    update.message.reply_text(
        "Signal Detected by IcarusBot: " + direction + " on " + pair)

    return SIGNALS


bots = []
updates = []
def start(bot, update):
    bots.append(bot)
    updates.append(update)
    update.message.reply_text(
        "Hi. I'm IcarusBot. I'm waiting for your input!")

    return SIGNALS


def readmail():
    print("Listening to email...")
    while True:
        time.sleep(1.5)
        m = imaplib.IMAP4_SSL(imap)
        m.login(user, pwd)
        m.select('"' + folder + '"')
        resp, items = m.search(None,
                               "NOT SEEN SUBJECT tradingview")
        items = items[0].split()
        for emailid in items:
            resp, data = m.fetch(emailid,
                                 "(RFC822)")
            email_body = data[0][1]
            mail = email.message_from_bytes(email_body)
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            direction = mail['Subject'].split()[3]
            pair = mail['Subject'].split()[2]
            for x in bots:
                bot = x
            for x in updates:
                update = x

            try:
                if "Close" not in direction:
                    # setup = Trade.get_or_create(pair)
                    m.store(emailid, '+FLAGS', '\Seen')
                    log(st + ' ' + direction + ' Triggered on ' + pair)
                    tele(direction, pair, bot, update)
                # Close Trade
                else:
                    direction = mail['Subject'].split()[4]
                    m.store(emailid, '+FLAGS', '\Seen')
                    tele(direction, pair, bot, update)
                    log(st + " Closed trade on " + pair)
            except Exception as e:
                log(e)

def cancel(bot, update):
    user = update.message.from_user
    update.message.reply_text('Bye! I hope we can talk again some day.')

    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    # print('Update "%s" caused error "%s"', update, error)
    pass


def main():
    threading.Thread(target=readmail).start()
    try:
        print("Listening to Telegram Channel...")
        updater = Updater(token)
        dp = updater.dispatcher
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],

            states={
                SIGNALS: []
            },

            fallbacks=[CommandHandler('cancel', cancel)]
        )

        dp.add_handler(conv_handler)
        dp.add_error_handler(error)
        updater.start_polling()
        updater.idle()
    except Exception as e:
        log(e)


if __name__ == '__main__':

    main()
