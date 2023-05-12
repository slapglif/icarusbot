from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import pytz

from app import engine, Base, db


class Trade(Base):
    __tablename__ = 'trade'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now(pytz.utc))
    nonce = Column(Float)
    pair = Column(String(2000))
    signal = Column(String(2000))
    price = Column(Float)
    volume = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    comment = Column(String(2000))

    @staticmethod
    def find(pair):
        return db.query(Trade).filter_by(pair=pair).first()

    @staticmethod
    def create(**kwargs):
        entry = Trade(**kwargs)
        db.add(entry)
        db.commit()
        return entry

    def __repr__(self):
        return f"<Trade(nonce='{self.nonce}', pair='{self.pair}', signal='{self.signal}')>"


Base.metadata.create_all(engine)
