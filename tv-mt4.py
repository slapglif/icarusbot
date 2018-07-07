import email, imaplib
import zmq
import random
import datetime, time
import logging

LOG_FILENAME = 'trades.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)

volume = '0.1'
user = ''
pwd = ''

print("Connecting to the mt4 server...")
logging.info("Connecting to the mt4 server...")

c = zmq.Context()
s = c.socket(zmq.REQ)
s.connect("tcp://127.0.0.1:5557")
r = c.socket(zmq.PULL)
r.connect("tcp://127.0.0.1:5558")


def generate_nonce(length=8):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])


def trade(signal,volume,pair):
    try:
        trade = 'TRADE|OPEN|' + signal + '|' + pair + '|0|0|0|IcarusBot Trade|' + generate_nonce() + '|' + volume
        s.send_string(trade, encoding='utf-8')
        print("Waiting for metatrader to respond...")
        logging.info("Waiting for metatrader to respond...")
        m = s.recv()
        print("Reply from server ", m)
    except Exception as e:
        print(e)
        logging.info(e)


print("Listening to email server...")
logging.info("Listening to email server...")


def readmail(volume):
    time.sleep(1.5)
    m = imaplib.IMAP4_SSL("imap.gmail.com")
    m.login(user, pwd)
    m.select('"[Gmail]/All Mail"')
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
                logging.info(st + ' Buy' + ' Triggered on ' + pair)
                trade('0', volume, pair)
            if mail['Subject'].split()[3] == "Sell":
                m.store(emailid, '+FLAGS', '\Seen')
                print(st + ' \x1b[6;30;41m' + 'Sell' + '\x1b[0m' + ' Triggered on ' + pair)
                logging.info(st + ' Sell' + ' Triggered on ' + pair)
                trade("1", volume, pair)
        except Exception as e:
            print(e)
            logging.info(e)


while True:
    try:
        readmail(volume)
    except Exception as e:
        print(e)
        logging.info(e)
