from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///trades.db', echo=False)
Session = sessionmaker(bind=engine)


class Trade(Base):

    __tablename__ = 'trade'

    id = Column(Integer, primary_key=True)
    nonce = Column(String(2000))
    pair = Column(String(2000))
    signal = Column(String(2000))

    def __repr__(self):
        return "<Trade(nonce='%s', pair='%s', signal='%s')>" % (
                                self.nonce, self.pair, self.signal)


Base.metadata.create_all(engine)
