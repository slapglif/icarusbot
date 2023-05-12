"""
This script is responsible for receiving signals from the tradingview
webhooks and sending them to the metatrader server.
"""
import email
import imaplib
import logging
import random
import time
from collections import namedtuple
from enum import Enum
from typing import Optional, Tuple

import zmq
from pydantic import BaseModel, Field

from settings import Config as config
from models import Trade
from app import Session
from app import logger
from app import logging

logger = logging.getLogger(__name__)

db = Session()


def generate_nonce(length: int = 8) -> str:
    """
    It generates a random string of numbers of a given length

    :param length: The length of the nonce, defaults to 8
    :type length: int (optional)
    :return: A string of random numbers.
    """
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


class TradeData(BaseModel):
    """
    pydantic model for handling trade data
    """

    action: Optional[str] = Field(exclude=True)
    signal: str
    pair: str
    nonce: Optional[str]
    volume: str
    price: Optional[str]
    stop_loss: Optional[str]
    take_profit: Optional[str]
    comment: Optional[str]


class TradeType(Enum):
    """
    Enum for trade types
    """

    open: str = "open"
    close: str = "close"


class TradeDirection(Enum):
    """
    Enum for trade directions
    """

    buy: str = "buy"
    sell: str = "sell"
    reverse: str = "reverse"


WAIT_METATRADER = "Waiting for metatrader to respond..."
SubjectInfo = namedtuple("SubjectInfo", ["direction", "pair", "close_direction"])

logger.info("Connecting to the mt4 server...")

logging.basicConfig(filename=config.log_filename, level=logging.INFO)


class TradeHandler(object):
    """
    Class for handling trades
    """

    def __init__(self) -> None:
        # Initializing the class.
        try:
            self.connection = zmq.Context(zmq.LINGER)
            self.connection.setsockopt(
                zmq.LINGER, 1000
            )  # ____POLICY: set upon instantiations
            self.connection.setsockopt(
                zmq.AFFINITY, 1
            )  # ____POLICY: map upon IO-type thread
            self.connection.setsockopt(zmq.RCVTIMEO, 2000)
            self.server = self.connection.socket(zmq.REQ)
            self.server.connect(config.socket1)
            self.reply = self.connection.socket(zmq.PULL)
            self.reply.connect(config.socket2)
        except zmq.error.ZMQBaseError as _ex:
            logger.info(str(_ex))

    def handle_trade(self, trade_data: TradeData) -> bool:
        """
        The handle_trade function is the main function that will be called by the TradeHandler.
        It takes in a trade_data object and returns a boolean value indicating whether or not
        the trade was successfully executed. The handle_trade function should contain all of your
        logic for determining when to execute trades, as well as any logic for executing those trades.

        Args:
            cls: Refer to the class itself
            trade_data: TradeData: Pass the trade data to the function

        Returns:
            A boolean
        """

        trade_action = self.determine_trade_action(trade_data)
        if trade_action is not TradeType.close:
            trade = Trade.find(trade_data.pair)
            if not trade:
                Trade.create(**trade_data.dict())

        if self.execute_trade_action(trade_action, trade_data):
            logger.info(f"{direction} Triggered on {trade_data.pair}")
            return True

    def determine_trade_action(self, trade_data: TradeData) -> str | None:
        """
        > If the direction is not "close", then return "cnr" if the setup is not
        hedging and the setup is not None and the setup has a nonce, otherwise return
        "trade". Otherwise, return "close" if the setup is not None and the setup has a
        nonce, otherwise return "trade"
        :param trade_data: The trade data
        """
        # trade_setup = Trade.find(trade_data.pair)
        logger.info(f"Determining trade action for {trade_data.pair}")
        logger.info(f"Trade data: {trade_data}")
        if trade := Trade.find(trade_data.pair):
            return TradeType.open.value
        return TradeType.close.value


    def execute_trade_action(self, trade_action: str, trade_data: TradeData) -> None:
        """
        If the trade_action is in the _trade_options
        dictionary, execute the function associated with
        the trade_action, otherwise do nothing.

        :param trade_action: The action to take on the trade. This can be one of the following:
        :param trade_data: The trade_data to be used in the trade.
        :return: The return value of the lambda function.
        """
        logger.info(f"Executing trade action: {trade_action}")
        _trade_options = {
            "open": lambda: self.trade(trade_data),
            "close_reverse": lambda: self.close_reverse(trade_data),
            "close": lambda: (self.close(trade_data)),
        }
        action: callable = _trade_options.get(trade_action)
        return action() if action else None


    def create_trade_payload(self, trade_data: TradeData) -> str:
        """
        It takes in a string, and returns a string
        :return: A string.
        """
        return (
            f"TRADE|{trade_data.action}|{trade_data.signal}|{trade_data.pair}"
            f"|{trade_data.price}|{trade_data.stop_loss}|{trade_data.take_profit}|"
            f"IcarusBot Trade|{trade_data.nonce}|{trade_data.volume}"
        )


    def trade(self, trade_data: TradeData) -> None:
        """
        It takes a signal, volume, pair, and nonce as arguments and sends a trade payload to the server
        """
        logger.info("Sending trade payload to server...")

        trade_payload = self.create_trade_payload(trade_data)
        logger.info(f"Trade payload: {trade_data}")
        message = self.execute_trade(trade_payload)
        logger.info(f"Reply from server {str(message)}")

    @classmethod
    def close(self, trade_data: TradeData) -> None:
        """
        It takes a signal, volume, and pair as arguments, and
        then sends a message to the metatrader server to close the trade

        """
        setup = Trade.find(trade_data.pair)
        if trade_data.nonce:
            trade_payload = self.create_trade_payload(trade_data)
            message = self.execute_trade(trade_payload)
            logger.info(f"Reply from server {message}")
            setup.nonce = None
            setup.signal = None
            db.flush()

    def modify(self, trade_data: TradeData) -> None:
        """
        It takes a signal, volume, and pair, and if there is a trade open
        for that pair, it sends a payload to the metatrader server to modify the trade
        """
        setup: Optional[Trade] = Trade.find(trade_data.pair)
        if setup is not None:
            trade_data.signal = "MODIFY"
            trade_payload: str = self.create_trade_payload(trade_data)
            message = self.execute_trade(trade_payload)
            logger.info(f"Reply from server {message}")

    def execute_trade(self, trade_payload):
        """
        The execute_trade function is used to send a trade request to the MetaTrader server.
        The function takes in a string of JSON data that contains all the necessary information for
        the MetaTrader server to execute the trade. The function then sends this payload over ZMQ, and waits for
        a response from the MetaTrader server. If there is no response within 10 seconds, an error message will be logged.

        Args:
            self: Represent the instance of the class
            trade_payload: Send a trade request to the metatrader server

        Returns:
            A string
        """
        logger.info(WAIT_METATRADER)
        self.server.send_string(trade_payload)
        return self.server.recv()

    def close_reverse(self, trade_data: TradeData) -> None:
        """
        > This function closes the current position and opens
        a new position in the opposite direction
        """
        self.close(trade_data)
        logger.info(f"Close and Reverse triggered on {trade_data.pair}")
        self.trade(trade_data)


class EmailHandler(object):
    """
    This class handles the email
    """

    def __init__(self, _trade_handler: TradeHandler) -> None:
        """
        This function takes in a trade handler and a volume and
        sets the trade handler and volume to the trade handler and volume of the class.

        :param _trade_handler: The trade handler object that will be used to execute the trade
        :type _trade_handler: TradeHandler
        """
        self.trade_handler = _trade_handler

    def read_mail(self) -> None:
        """
        It connects to the email server, selects the folder,
        searches for unread emails with the subject "tradingview",
        and then processes each email
        """
        time.sleep(1.5)
        imap = imaplib.IMAP4_SSL(config.imap)
        imap.login(config.user, config.pwd)
        imap.select(f'"{config.folder}"')
        resp, items = imap.search(None, "NOT SEEN SUBJECT tradingview")
        items = items[0].split()

        for email_id in items:
            response: Tuple[Optional[str], Optional[list]] = imap.fetch(
                email_id, "(RFC822)"
            )
            email_body = response[1][0][1]
            mail = email.message_from_bytes(email_body)
            subject_info: SubjectInfo = self.parse_subject(mail)

            self.process_email_subject(subject_info, email_id, imap)

    def process_email_subject(
            self, subject_info: SubjectInfo, email_id: str, imap: imaplib.IMAP4_SSL
    ) -> None:
        """
        It takes in a subject line, an email id, and an IMAP connection, and then
        it determines whether to trade, close, or close and reverse based on the
         subject line, and then it
        executes the trade

        :param subject_info: SubjectInfo = This is the object that contains the information from the email subject
        :type subject_info: SubjectInfo
        :param email_id: The email id of the email that was fetched
        :type email_id: str
        :param imap: imaplib.IMAP4_SSL
        :type imap: imaplib.IMAP4_SSL
        """

        direction = subject_info.direction
        pair = subject_info.pair
        signal = "0" if direction == "Buy" else "1"

        trade_data = TradeData(
            signal=signal,
            pair=pair,
            target_symbol=config.target_symbol,
            nonce=generate_nonce(),
            volume=config.volume,
            action=None,
        )
        Trade.find(pair) or Trade.create(
            **trade_data.dict()
        ) if "Close" not in direction else None
        trade_action = self.trade_handler.determine_trade_action(trade_data)
        if self.trade_handler.execute_trade_action(trade_action, trade_data):
            imap.store(email_id, "+FLAGS", "\\Seen")
            logger.info(f"{direction} Triggered on {pair}")

    @classmethod
    def parse_subject(self, mail: email.message.Message) -> SubjectInfo:
        """
        It parses the subject line of an email and returns a SubjectInfo object

        :param cls: The class that is calling the method
        :param mail: email.message.Message
        :type mail: email.message.Message
        """
        subject = mail["Subject"]
        subject_parts = subject.split()
        direction = subject_parts[3]
        pair = subject_parts[2]
        close_direction = subject_parts[4] if "Close" in direction else None

        return SubjectInfo(direction, pair, close_direction)
