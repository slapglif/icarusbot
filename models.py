from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///trades.db', echo=False)
Session = sessionmaker(bind=engine, autocommit=True)
db = Session()

class Trade(Base):

    __tablename__ = 'trade'

    id = Column(Integer, primary_key=True)
    nonce = Column(String(2000))
    pair = Column(String(2000))
    signal = Column(String(2000))
    price = Column(String(2000))
    tp = Column(String(2000))
    sl = Column(String(2000))

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
