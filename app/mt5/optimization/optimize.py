import json
import threading
from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from pydantic import BaseModel
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.so_de import DE
from pymoo.factory import get_problem, get_sampling, get_crossover, get_mutation
from pymoo.optimize import minimize
from pymoo.model.problem import Problem
import MetaTrader5 as mt5
from app.mt5.optimization.timeframes import Timeframes


# build out our strategy class
class BaseStrategy:

    def __init__(self, symbol, data):
        self.symbol = symbol
        self.data = data
        self.data['buySignal'] = 0
        self.data['sellSignal'] = 0
        self.data['position'] = 0
        self.data['returns'] = 0
        self.parameters = []
        # Define the range of the parameters to optimize
        self.MinimumEMA_range = (5, 15)
        self.stopLoss_range = (0.001, 0.01)
        self.takeProfit_range = (0.01, 0.1)
        self.wickBuyThreshold_range = (0.5, 0.9)
        self.wickSellThreshold_range = (0.5, 0.9)

        self.MinimumEMA = 0
        self.stopLoss = 0
        self.takeProfit = 0
        self.wickBuyThreshold = 0
        self.wickSellThreshold = 0
        self.MedianEMA = 0
        self.MaximumEMA = 0


        self.bounds = np.array([self.MinimumEMA_range, self.stopLoss_range, self.takeProfit_range, self.wickBuyThreshold_range, self.wickBuyThreshold_range])
        self.strategy_df = self.build_strategy()


def signal(self, parameters: list):
    MinimumEMA, MedianEMA, MaximumEMA, wickBuyThreshold, wickSellThreshold = parameters
    # get current values

    # Calculate EMAs
    self.data['MinimumEMA'] = self.data['close'].ewm(span=MinimumEMA, adjust=False).mean()
    self.data['MedianEMA'] = self.data['close'].ewm(span=MedianEMA, adjust=False).mean()
    self.data['MaximumEMA'] = self.data['close'].ewm(span=MaximumEMA, adjust=False).mean()

    # Calculate wick sizes
    self.data['bullishWickTopSize'] = self.data['close'] - self.data['high']
    self.data['bullishWickBottomSize'] = self.data['low'] - self.data['open']

    # Buy conditions
    self.data['buySeup'] = (self.data['bullishWickTopSize'] < (self.data['high'] - self.data['low']) - ((self.data['high'] - self.data['low']) * wickBuyThreshold)) & (
            self.data['close'] < self.data['close'].shift())
    self.data['sellSetup'] = (self.data['bullishWickBottomSize'] < (self.data['high'] - self.data['low']) + ((self.data['high'] - self.data['low']) * wickSellThreshold)) & (
            self.data['close'] > self.data['close'].shift())

    # Implement your strategy here using the parameters from x

    self.data['buySignal'] = (self.data['buySeup'] &
                              (self.data['close'] < self.data['MinimumEMA']) &
                              (self.data['close'] > self.data['MedianEMA']))

    self.data['sellSignal'] = (self.data['sellSetup'] &
                               (self.data['close'] > self.data['MinimumEMA']) &
                               (self.data['close'] < self.data['MedianEMA']))

    # return a signal for consumption
    return self.data['buySignal'], self.data['sellSignal']


def build_strategy(self, data: pd.DataFrame = None):
    # Calculate EMAs
    self.data['MinimumEMA'] = self.data['close'].ewm(span=MinimumEMA, adjust=False).mean()
    self.data['MedianEMA'] = self.data['close'].ewm(span=MedianEMA, adjust=False).mean()
    self.data['MaximumEMA'] = self.data['close'].ewm(span=MaximumEMA, adjust=False).mean()

    # Calculate wick sizes
    self.data['bullishWickTopSize'] = self.data['close'] - self.data['high']
    self.data['bullishWickBottomSize'] = self.data['low'] - self.data['open']

    # Buy conditions
    self.data['buySeup'] = (self.data['bullishWickTopSize'] < (self.data['high'] - self.data['low']) - ((self.data['high'] - self.data['low']) * wickBuyThreshold)) & (
            self.data['close'] < self.data['close'].shift())
    self.data['sellSetup'] = (self.data['bullishWickBottomSize'] < (self.data['high'] - self.data['low']) + ((self.data['high'] - self.data['low']) * wickSellThreshold)) & (
            self.data['close'] > self.data['close'].shift())

    # Implement your strategy here using the parameters from x

    self.data['buySignal'] = (self.data['buySeup'] &
                              (self.data['close'] < self.data['MinimumEMA']) &
                              (self.data['close'] > self.data['MedianEMA']))

    self.data['sellSignal'] = (self.data['sellSetup'] &
                               (self.data['close'] > self.data['MinimumEMA']) &
                               (self.data['close'] < self.data['MedianEMA']))

    return self.data


class MyProblem(Problem):

    def __init__(self, symbol, data):
        super().__init__(n_var=5,
                         n_obj=3,
                         n_constr=0,
                         xl=np.array([5, 0.001, 0.001, 0.1, 0.1]),
                         xu=np.array([100, 0.05, 0.05, 1, 1]))
        self.symbol = symbol
        self.data = data
        self.strategy = BaseStrategy(symbol, data)

    def _calculate_objectives(self, parameters: List[float]):
        self.data = self.strategy.build_strategy(parameters)

        # Assume that we buy/sell 1 unit whenever we get a buy/sell signal
        self.data['position'] = self.data['buySignal'].astype(int) - self.data['sellSignal'].astype(int)

        # Calculate returns
        self.data['returns'] = self.data['position'].shift() * (self.data['close'] - self.data['close'].shift())

        # Calculate the objectives
        net_profit = self.data['returns'].sum()

        # The Sharpe ratio is a measure of risk-adjusted return
        # We'll assume a risk-free rate of 0
        # Also, we'll use the standard deviation of returns as our measure of risk
        sharpe_ratio = self.data['returns'].mean() / self.data['returns'].std()

        # Total number of trades
        number_of_trades = self.data['buySignal'].sum() + self.data['sellSignal'].sum()

        return [-net_profit, -sharpe_ratio, number_of_trades]

    def _evaluate(self, x, out, *args, **kwargs):
        out["F"] = np.row_stack([self._calculate_objectives(xi) for xi in x])


# Initialize MT5
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    quit()

# List of symbols to optimize
symbols = ["EURUSD", "GBPUSD", "USDJPY"]

for symbol in symbols:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 5000)

    # Prepare data
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data = data.set_index('time')

    # pick an optimization algorithm
    # in this case were using Genetic Algorithm
    # 1. NSGA2
    # 2. DE
    # 3. PSO
    # 4. CMAES
    # 5. IBEA
    # 6. MOEAD
    # 7. EpsMOEA
    # 8. RNSGA3
    # 9. RNSGA2
    # 10. RVEA
    # 11. NSGA3
    # 12. OMOPSO
    # 13. SMPSO
    # 14. GDE3

    algorithm = NSGA2(
        pop_size=40,
        n_offsprings=10,
        sampling=get_sampling("real_random"),
        crossover=get_crossover("real_sbx", prob=0.9, eta=15),
        mutation=get_mutation("real_pm", eta=20),
        eliminate_duplicates=True
    )

    # Define the problem
    problem = MyProblem(symbol, data)

    # Perform the optimization
    res = minimize(problem,
                   algorithm,
                   ("n_gen", 100),
                   verbose=True)

    # algorithm = DE(pop_size=100)
    # # Run optimization
    # res = minimize(problem,
    #                algorithm,
    #                ("n_gen", 100),
    #                verbose=True,
    #                seed=1)

    print("Best solution found: \nX = %s\nF = %s" % (res.X, res.F))
    print(f"Function value: {res.F}")
    print(f"Constraint violation: {res.CV}")
    print(f"Running time: {res.exec_time}")
    print(f"Number of generations: {res.algorithm.n_gen}")
    print(f"Stopping criterion: {res.algorithm.stopping_criterion}")

    # Plot the results
    fig, ax = plt.subplots()
    ax.scatter(res.F[:, 0], res.F[:, 1], s=30, c="red")
    ax.scatter(res.F[:, 0], res.F[:, 1], s=30, c="red")
    ax.set_xlabel("$f_1(x)$")
    ax.set_ylabel("$f_2(x)$")
    plt.show()

    # Plot the results
    fig, ax = plt.subplots()
    ax.scatter(res.F[:, 0], res.F[:, 2], s=30, c="red")
    ax.scatter(res.F[:, 0], res.F[:, 2], s=30, c="red")
    ax.set_xlabel("$f_1(x)$")
    ax.set_ylabel("$f_3(x)$")
    plt.show()


    # store the best values as a pydantic model

    class BestValues(BaseModel):
        MinimumEMA: float
        MedianEMA: float
        MaximumEMA: float
        stopLoss: float
        takeProfit: float
        wickBuyThreshold: float
        wickSellThreshold: float


    best_values = BestValues(
        MinimumEMA=res.X[0],
        MedianEMA=res.X[1],
        MaximumEMA=res.X[2],
        stopLoss=res.X[3],
        takeProfit=res.X[4],
        wickBuyThreshold=res.X[5],
        wickSellThreshold=res.X[6]
    )

    # save the best values to a json file
    with open(f"best_values_{symbol}.json", "w") as f:
        json.dump(best_values.dict(), f)


# build our strategy class to live trade with

class Strategy(BaseStrategy):

    def __init__(self, symbol, data, MinimumEMA, MedianEMA, MaximumEMA, stopLoss, takeProfit, wickBuyThreshold, wickSellThreshold):
        self.wickTrades = 0
        self.symbol = symbol
        self.data = data
        self.MinimumEMA = MinimumEMA
        self.MedianEMA = MedianEMA
        self.MaximumEMA = MaximumEMA
        self.stopLoss = stopLoss
        self.takeProfit = takeProfit
        self.wickBuyThreshold = wickBuyThreshold
        self.wickSellThreshold = wickSellThreshold
        self.position = 0
        self.buySignal = 0
        self.sellSignal = 0
        self.buyPrice = 0
        self.sellPrice = 0

    def buy(self, price):
        # implement the buy order logic for mt5
        self.position = 1
        self.buyPrice = price
        self.buySignal = 1

        # return a buy signal for use with the mt5 order logic
        return 1

    def sell(self):
        # implement the sell order logic for mt5
        self.position = -1
        self.sellSignal = 1

        # return a sell signal for use with the mt5 order logic
        return -1

    def close(self, price):

        if self.position == 1:
            self.buySignal = self.buy()
            self.profit = self.profit + (price - self.buyPrice)
            self.buyPrice = 0

        elif self.position == -1:
            self.profit = self.profit + (self.sellPrice - price)
            self.sellSignal = self.sell()
            self.sellPrice = 0

    def wickBuy(self, price):

        self.position = 1
        self.wickBuyPrice = price
        self.wickBuySignal = 1

    def wickSell(self, price):

        self.position = -1
        self.wickSellPrice = price
        self.wickSellSignal = 1

    def wickClose(self, price):

        if self.position == 1:
            self.wickBuySignal = self.wickIsClosed()
            self.wickProfit = self.wickProfit + (price - self.wickBuyPrice)
            self.wickBuyPrice = 0

        elif self.position == -1:
            self.wickProfit = self.wickProfit + (self.wickSellPrice - price)
            self.wickSellSignal = self.wickIsClosed()
            self.wickSellPrice = 0

    def wickIsClosed(self):
        self.wickTrades = self.wickTrades + 1
        self.position = 0
        return 0

    # STREAM the mt4 data in threads and run the strategy in the main thread
    class Interval(BaseModel):
        days: int = 1
        hours: int = 0
        minutes: int = 0
        seconds: int = 0

    def get_ticker_data(self, pair: str, interval: Interval.days = 30):
        """
        get the stream of data for the given pair
        and return it to the thread (async?)
        ensure we get the data for each timeframe and
        store each timeframe into a dataframe so we can iterate them
        the best aggregate result later
        """

        def _process_data(_pair_data: pd.DataFrame):
            pair_data = pd.DataFrame(_pair_data)
            pair_data['time'] = pd.to_datetime(pair_data['time'], unit='s')
            pair_data.set_index('time', inplace=True)
            pair_data = pair_data.drop(['spread', 'real_volume'], axis=1)
            pair_data.columns = ['open', 'high', 'low', 'close', 'tick_volume']
            pair_data = pair_data.astype(float)
            return pair_data

        timeframes: List[str] = list(Timeframes().dict().values())
        # get the data from mt5
        for MTTimeFrame in timeframes:
            # timeframes

            pair_data = mt5.copy_rates_from(pair,
                                            MTTimeFrame,
                                            datetime.now() - timedelta(**interval),
                                            datetime.now())

            # get the data for the pair

            pair_data = _process_data(pair_data)
            # return the data
            return pair_data

    def run(self):
        """
        this method will be used to launch the worker threads which process the data
        asynchronously and then return the results to the main thread for processing
        """
        # get the data for the pair
        data = self.get_ticker_data(self.symbol)
        # run the strategy
        self.build_strategy()
        #  strategy buiilds the strategy into our state machine
        # and then we can use the state machine to trade
        # the strategy will be run in a thread and the
        # state machine will be run in the main thread
        # we will use the state machine to trade the strategy

    ### we have already built a Strategy class and initalized it as
    # our state machine - now if we use the build_strategy method
    # we can generate the strategy tick for the last passed data and
    # and optional interval - it will then retreive the data for the
    # given timeframe and then run the strategy on that data and return
    # the result to the main thread for processing
