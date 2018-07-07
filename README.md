# tv-mt4
## Requirements
Metatrder 4
https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe?utm_source=www.metatrader4.com&utm_campaign=download

ZMQ Server for MT4
https://github.com/dingmaotu/mql-zmq

# How to use
Configure Email server under imap settings, including user and pw Run ZMQ server on mt4 as a script, set up alerts on tradingview.com with the following format:

description:

```PAIR Signal```

for example

```EURUSD Sell```
