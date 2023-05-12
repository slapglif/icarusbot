# Overview
IcarusBot is an email-driven trading system that listens to incoming trade signals from TradingView and automatically executes trades on the MetaTrader platform. The bot monitors a specified email account, parses trade signal emails, and processes the email subject to determine the appropriate trading action. It then delegates the trading action to a trade handler responsible for communicating with the MetaTrader platform.

The system is composed of the following components:

* **EmailHandler**: Handles incoming emails, extracts relevant information, and processes trading signals.
* **TradeHandler**: Manages communication with the MetaTrader platform and executes the trading actions.
* **Trade**: Represents a trade setup, including information about the trading pair, direction, and nonce.
* **SubjectInfo**: A namedtuple that holds relevant information extracted from an email subject. 

## Refactoring Motivation
The initial implementation of the IcarusBot trading system contained several issues related to code readability, maintainability, and best practices. The primary goal of our refactor was to:

* **Improve code readability**: We broke down complex code blocks into smaller, more manageable functions, making it easier to understand the system's logic and purpose.
* **Reduce cognitive complexity**: We simplified nested conditions and loops, which helped make the code more approachable and easier to reason about.
* **Leverage modern Python features**: We introduced the use of f-strings, type annotations, and namedtuples to make the code more expressive and easier to maintain.
* **Improve error handling**: We addressed potential issues related to list access, making the code more robust and less prone to errors.
With these improvements, the IcarusBot trading system is now more maintainable and easier for others to understand and contribute to.

## Requirements
Metatrder 4
https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe?utm_source=www.metatrader4.com&utm_campaign=download

ZMQ Server for MT4
https://github.com/dingmaotu/mql-zmq

Make sure you set up your .env file!

# Usage
To use the IcarusBot trading system, instantiate an EmailHandler object with the appropriate trade handler and volume, and then call the readmail method to start monitoring the specified email account for trade signals.\
```
trade_handler = TradeHandler()
email_handler = EmailHandler(trade_handler)
email_handler.readmail()
```
Configure Email server under imap settings, including user and pw Run ZMQ server on mt4 as a script, set up alerts on tradingview.com with the following format:



```PAIR Signal```

for example

```EURUSD Sell```

The system will continuously monitor the specified email account, parse incoming trade signals, and execute trades on the MetaTrader platform accordingly.

The system will continuously monitor the specified email account, parse incoming trade signals, and execute trades on the MetaTrader platform accordingly.