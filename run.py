import imaplib
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.bot.tv_mt4 import TradeHandler, EmailHandler, TradeData
import uvicorn
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse("/docs")


class TradeExecutionResponse(BaseModel):
    """
    Trade execution response
    """
    executed: bool
    message: str


@app.post("/trade", response_model=TradeExecutionResponse)
def trade(context: TradeData):
    trade_handler = TradeHandler()
    executed: bool = trade_handler.handle_trade(context)
    return (
        TradeExecutionResponse(
            executed=True,
            message=f"Trade executed on {context.pair} at {context.price}",
        )
        if executed
        else TradeExecutionResponse(
            executed=False, message="Trade not executed"
        )
    )


# uvicorn.run(app, host="127.0.0.1", port=8000)

from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters

register_matplotlib_converters()
import MetaTrader5 as mt5

# connect to MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    mt5.shutdown()

# request connection status and parameters
print(mt5.terminal_info())
# get data on MetaTrader 5 version
print(mt5.version())

# # request 1000 ticks from EURAUD
#euraud_ticks = mt5.copy_ticks_from("EURAUD", mt5.TIMEFRAME_M1, 0, 1000)
# # request ticks from AUDUSD within 2019.04.01 13:00 - 2019.04.02 13:00
# audusd_ticks = mt5.copy_ticks_range("AUDUSD", datetime(2020, 1, 27, 13), datetime(2020, 1, 28, 13), mt5.COPY_TICKS_ALL)[:-10]

# get bars from different symbols in a number of ways
# eurusd_rates = mt5.copy_rates_from("EURUSD", mt5.TIMEFRAME_M1, datetime(2020, 1, 28, 13), 1000)[:-10]
# eurgbp_rates = mt5.copy_rates_from_pos("EURGBP", mt5.TIMEFRAME_M1, 0, 1000)
# eurcad_rates = mt5.copy_rates_range("EURCAD", mt5.TIMEFRAME_M1, datetime(2020, 1, 27, 13), datetime(2020, 1, 28, 13))

# shut down connection to MetaTrader 5

ticks = mt5.copy_ticks_from("EURAUD", mt5.TIMEFRAME_M1, 0, 1000)
# DATA
print('euraud_ticks(', len(ticks), ')')
for val in ticks[:10]:
    print(val)
#
# print('audusd_ticks(', len(audusd_ticks), ')')
# for val in audusd_ticks[:10]: print(val)
#
# print('eurusd_rates(', len(eurusd_rates), ')')
# for val in eurusd_rates[:10]: print(val)
#
# print('eurgbp_rates(', len(eurgbp_rates), ')')
# for val in eurgbp_rates[:10]: print(val)

# print('eurcad_rates(', len(eurcad_rates), ')')
# for val in eurcad_rates[:10]: print(val)

# PLOT
# create DataFrame out of the obtained data
ticks_frame = pd.DataFrame(ticks)
# convert time in seconds into the datetime format
ticks_frame['time'] = pd.to_datetime(ticks_frame['time'], unit='s')
# display ticks on the chart
plt.plot(ticks_frame['time'], ticks_frame['ask'], 'r-', label='ask')
plt.plot(ticks_frame['time'], ticks_frame['bid'], 'b-', label='bid')

# display the legends
plt.legend(loc='upper left')

# add the header
plt.title('EURAUD ticks')

# display the chart
plt.show()

mt5.shutdown()

#
#
# if __name__ == "__main__":
#     # log("Listening to email server...")
#
#     trade_handler = TradeHandler()
#     # email_handler = EmailHandler(trade_handler)
#     # while True:
#     #     try:
#     #         email_handler.read_mail()
#     #     except imaplib.IMAP4.error as _e:
#     #         log(str(_e))
