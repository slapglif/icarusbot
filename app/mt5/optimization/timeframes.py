from enum import Enum
from typing import List, Any

from pydantic import BaseModel
import MetaTrader5 as mt5

class Timeframes(BaseModel):
    m1: Any = mt5.TIMEFRAME_M1
    m2: Any = mt5.TIMEFRAME_M2
    m3: Any = mt5.TIMEFRAME_M3
    m4: Any = mt5.TIMEFRAME_M4
    m5: Any = mt5.TIMEFRAME_M5
    m6: Any = mt5.TIMEFRAME_M6
    m10: Any = mt5.TIMEFRAME_M10
    m12: Any = mt5.TIMEFRAME_M12
    m15: Any = mt5.TIMEFRAME_M15
    m20: Any = mt5.TIMEFRAME_M20
    m30: Any = mt5.TIMEFRAME_M30
    h1: Any = mt5.TIMEFRAME_H1
    h2: Any = mt5.TIMEFRAME_H2
    h3: Any = mt5.TIMEFRAME_H3
    h4: Any = mt5.TIMEFRAME_H4
    h6: Any = mt5.TIMEFRAME_H6
    h8: Any = mt5.TIMEFRAME_H8
    h12: Any = mt5.TIMEFRAME_H12
    d1: Any = mt5.TIMEFRAME_D1
    w1: Any = mt5.TIMEFRAME_W1
    mn1: Any = mt5.TIMEFRAME_MN1

    # handle exceptions by showing the expected choice and list of timeframes
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._validate_timeframes()

    def _validate_timeframes(self):
        for key, value in self.__dict__.items():
            if not isinstance(value, Enum):
                raise ValueError(f"Invalid timeframe {value} for {key}")

    def get_timeframes(self) -> List[Any]:
        return [value for key, value in self.__dict__.items() if not isinstance(value, Enum)]

    def get_timeframes_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if not isinstance(value, Enum)}






modifying_schema = Timeframes.schema()
modifying_schema['title'] = 'Timeframes'
modifying_schema['description'] = 'Timeframes for MetaTrader5 trading platform'
Timeframes.update_forward_refs()
Timeframes.schema = modifying_schema

