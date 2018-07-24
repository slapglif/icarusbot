import email, imaplib
import zmq
import random
import datetime, time
import logging
import json
import models
from models import Trade

db = models.Session()

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


def green(msg):
    return ' \x1b[6;30;42m' + msg + '\x1b[0m'


def red(msg):
    return ' \x1b[6;30;41m' + msg + '\x1b[0m'


def cyan(msg):
    return ' \x1b[6;30;36m' + msg + '\x1b[0m'


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
        setup = db.query(Trade).filter_by(pair=pair).first()
        setup.nonce = nonce
        setup.pair = pair
        setup.signal = direction
        db.commit()
    except Exception as e:
        log(e)


def close(signal, volume, pair):
    try:
        setup = db.query(Trade).filter_by(pair=pair).first()
        if setup.nonce is not None:
            trade = 'TRADE|CLOSE|' + signal + '|' + pair + '|0|' + STOPLOSS + '|' + TAKEPROFIT + \
                    '|IcarusBot Trade|' + setup.nonce + '|' + volume
            s.send_string(trade, encoding='utf-8')
            log("Waiting for metatrader to respond...")
            m = s.recv()
            log("Reply from server " + m.decode('utf-8'))
            setup.nonce = None
            db.commit()
    except Exception as e:
        log(e)


def modify(signal, volume, pair):
    try:
        setup = db.query(Trade).filter_by(pair=pair).first()
        if setup.nonce is not None:
            trade = 'TRADE|MODIFY|' + signal + '|' + pair + '|0|' + STOPLOSS + '|' + TAKEPROFIT + \
                    '|IcarusBot Trade|' + setup.nonce + '|' + volume
            s.send_string(trade, encoding='utf-8')
            log("Waiting for metatrader to respond...")
            m = s.recv()
            log("Reply from server " + m.decode('utf-8'))
    except Exception as e:
        log(e)


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

        # Open Trade

        try:
            pair = mail['Subject'].split()[2]
            if mail['Subject'].split()[3] == "Buy":
                setup = db.query(Trade).filter_by(pair=pair).first()
                if setup is None:
                    entry = Trade(pair=pair, signal=mail['Subject'].split()[3])
                    db.add(entry)
                    db.commit()
                m.store(emailid, '+FLAGS', '\Seen')
                print(st + green("Buy") + ' Triggered on ' + pair)
                log(st + ' Buy' + ' Triggered on ' + pair)
                if hedging == "0":
                    setup = db.query(Trade).filter_by(pair=pair).first()
                    if setup.nonce is not None:
                        close('1', volume, pair)
                        log("Close and Reverse triggered on " + pair)
                        trade('0', volume, pair, nonce)
                        if pair == "SPX500":
                            trade("0", volume, "DJI30", generate_nonce())
                            log(st + ' Buy' + ' Triggered on ' + "DJI30")
                    else:
                        trade("0", volume, pair, nonce)
                        if pair == "SPX500":
                            trade("0", volume, "DJI30", generate_nonce())
                            log(st + ' Buy' + ' Triggered on ' + "DJI30")
                else:
                    trade('0', volume, pair,  nonce)
                    if pair == "SPX500":
                        trade("0", volume, "DJI30", generate_nonce())
                        log(st + ' Buy' + ' Triggered on ' + "DJI30")
            if mail['Subject'].split()[3] == "Sell":
                setup = db.query(Trade).filter_by(pair=pair).first()
                if setup is None:
                    entry = Trade(pair=pair, signal=mail['Subject'].split()[3])
                    db.add(entry)
                    db.commit()
                m.store(emailid, '+FLAGS', '\Seen')
                print(st + red("Sell") + ' Triggered on ' + pair)
                log(st + ' Sell' + ' Triggered on ' + pair)
                if hedging == "0":
                    setup = db.query(Trade).filter_by(pair=pair).first()
                    if setup.nonce is not None:
                        close('0', volume, pair)
                        log("Close and Reverse triggered on " + pair)
                        trade('1', volume, pair, nonce)
                        if pair == "SPX500":
                            trade("1", volume, "DJI30", generate_nonce())
                            log(st + ' Sell' + ' Triggered on ' + "DJI30")
                    else:
                        trade("1", volume, pair, nonce)
                        if pair == "SPX500":
                            trade("1", volume, "DJI30", generate_nonce())
                            log(st + ' Sell' + ' Triggered on ' + "DJI30")
                else:
                    trade("1", volume, pair, nonce)
                    if pair == "SPX500":
                        trade("1", volume, "DJI30", generate_nonce())
                        log(st + ' Sell' + ' Triggered on ' + "DJI30")
        except Exception as e:
            log(e)

        # Close Trade

        try:
            pair = mail['Subject'].split()[2]
            if mail['Subject'].split()[3] == "Close":
                direction = mail['Subject'].split()[4]
                setup = db.query(Trade).filter_by(pair=pair).first()
                if setup.nonce is not None:
                    if setup.signal == direction:
                        m.store(emailid, '+FLAGS', '\Seen')
                        print(st + cyan("Close") + ' Triggered on ' + pair)
                        log(st + ' Close' + ' Triggered on ' + pair)
                        if pair == "SPX500":
                            close("0", volume, "DJI30")
                            log(st + ' Close' + ' Triggered on ' + "DJI30")
                        close('0', volume, pair)
        except Exception as e:
            log(e)


while True:
    try:
        readmail(volume)
    except Exception as e:
        log(e)
