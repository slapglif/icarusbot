import email, imaplib
import zmq
import random
import datetime, time
import logging
import json

with open('config.json') as json_data_file:
        config = json.load(json_data_file)

volume = config['volume']
debug = config['debug']
LOG_FILENAME = config['LOG_FILENAME']
imap = config['imap']
user = config['user']
pwd = config['pwd']
folder = config['folder']
STOPLOSS = config['STOPLOSS']
TAKEPROFIT = config['TAKEPROFIT']


def log(msg):
    if debug == "1":
        print(msg)
    logging.info(msg)


log("Connecting to the mt4 server...")

# INIT
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
try:
    c = zmq.Context()
    s = c.socket(zmq.REQ)
    s.connect(config['socket1'])
    r = c.socket(zmq.PULL)
    r.connect(config['socket2'])
except Exception as e:
    log(e)


def generate_nonce(length=8):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def trade(signal, volume, pair):
    try:
        trade = 'TRADE|OPEN|' + signal + '|' + pair + '|0|' + STOPLOSS + '|' + TAKEPROFIT + \
                '|IcarusBot Trade|' + generate_nonce() + '|' + volume
        s.send_string(trade, encoding='utf-8')
        log("Waiting for metatrader to respond...")
        m = s.recv()
        log("Reply from server " + m)
    except Exception as e:
        log(e)


log("Listening to email server...")


def readmail(volume):
    time.sleep(1.5)
    m = imaplib.IMAP4_SSL(imap)
    m.login(user, pwd)
    m.select('"' + folder + '"')
    resp, items = m.search(None,
                           "NOT SEEN FROM tradingview")
    items = items[0].split()
    for emailid in items:
        resp, data = m.fetch(emailid,
                             "(RFC822)")
        email_body = data[0][1]
        mail = email.message_from_bytes(email_body)
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        try:
            pair = mail['Subject'].split()[2]
            if mail['Subject'].split()[3] == "Buy":
                m.store(emailid, '+FLAGS', '\Seen')
                print(st + ' \x1b[6;30;42m' + 'Buy' + '\x1b[0m' + ' Triggered on ' + pair)
                log(st + ' Buy' + ' Triggered on ' + pair)
                trade('0', volume, pair)
                if pair == "SPX500":
                    trade("0", volume, "DJI30")
                    log(st + ' Buy' + ' Triggered on ' + "DJI30")
            if mail['Subject'].split()[3] == "Sell":
                m.store(emailid, '+FLAGS', '\Seen')
                print(st + ' \x1b[6;30;41m' + 'Sell' + '\x1b[0m' + ' Triggered on ' + pair)
                log(st + ' Sell' + ' Triggered on ' + pair)
                trade("1", volume, pair)
                if pair == "SPX500":
                    trade("1", volume, "DJI30")
                    log(st + ' Buy' + ' Triggered on ' + "DJI30")
        except Exception as e:
            log(e)


while True:
    try:
        readmail(volume)
    except Exception as e:
        log(e)
