import email, imaplib
import zmq
import random
import datetime, time
import logging
import json
from models import Trade, Session

db = Session()

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
hedging = config['hedge']


def generate_nonce(length=8):
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


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


def trade(signal, volume, pair, nonce):
    try:
        trade = 'TRADE|OPEN|' + signal + '|' + pair + '|0|' + STOPLOSS + '|' + TAKEPROFIT + \
                '|IcarusBot Trade|' + nonce + '|' + volume
        s.send_string(trade, encoding='utf-8')
        log("Waiting for metatrader to respond...")
        m = s.recv()
        log("Reply from server " + m.decode('utf-8'))
        if signal == "0":
            direction = 'Long'
        else:
            direction = 'Short'
        setup = Trade.get_or_create(pair)
        setup.nonce = nonce
        setup.pair = pair
        setup.signal = direction
        db.commit()
        if pair == "SPX500":
            trade(signal, volume, "DJI30", generate_nonce())
            log('Sell' + ' Triggered on ' + "DJI30")
    except Exception as e:
        log(e)


def close(signal, volume, pair):
    try:
        setup = Trade.find(pair)
        if setup.nonce is not None:
            trade = 'TRADE|CLOSE|' + signal + '|' + pair + '|0|' + STOPLOSS + '|' + TAKEPROFIT + \
                    '|IcarusBot Trade|' + setup.nonce + '|' + volume
            s.send_string(trade, encoding='utf-8')
            log("Waiting for metatrader to respond...")
            m = s.recv()
            log("Reply from server " + m.decode('utf-8'))
            setup.nonce = None
            setup.signal = None
            db.commit()
    except Exception as e:
        log(e)


def modify(signal, volume, pair):
    try:
        setup = Trade.find(pair)
        if setup.nonce is not None:
            trade = 'TRADE|MODIFY|' + signal + '|' + pair + '|0|' + STOPLOSS + '|' + TAKEPROFIT + \
                    '|IcarusBot Trade|' + setup.nonce + '|' + volume
            s.send_string(trade, encoding='utf-8')
            log("Waiting for metatrader to respond...")
            m = s.recv()
            log("Reply from server " + m.decode('utf-8'))
    except Exception as e:
        log(e)


def cnr(signal, volume, pair, nonce):
    close(signal, volume, pair)
    log("Close and Reverse triggered on " + pair)
    trade(signal, volume, pair, nonce)


log("Listening to email server...")


def readmail(volume):
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
        nonce = generate_nonce()
        if mail['Subject'].split()[3] == "Buy":
            signal = "0"
        else:
            signal = "1"
        pair = mail['Subject'].split()[2]
        try:
            setup = Trade.get_or_create(pair)
            m.store(emailid, '+FLAGS', '\Seen')
            log(st + ' Buy' + ' Triggered on ' + pair)
            if hedging == "0":
                if setup.nonce is not None:
                    cnr(signal, volume, pair, nonce)
                else:
                    trade(signal, volume, pair, nonce)
            else:
                trade(signal, volume, pair, nonce)
        # Close Trade
            if mail['Subject'].split()[3] == "Close":
                direction = mail['Subject'].split()[4]
                setup = Trade.find(pair)
                if setup is not None:
                    if setup.signal == direction:
                        m.store(emailid, '+FLAGS', '\Seen')
                        close(signal, volume, pair)
                        log(st + " Closed trade on " + pair)
        except Exception as e:
            log(e)


while True:
    try:
        readmail(volume)
    except Exception as e:
        log(e)
