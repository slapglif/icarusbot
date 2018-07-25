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
    price = Column(String(2000))
    tp = Column(String(2000))
    sl = Column(String(2000))

    @staticmethod
    def get_or_create(pair):
        setup = Session().query(Trade).filter_by(pair=pair).first()
        if setup is None:
            entry = Trade(pair=pair)
            Session().add(entry)
        return setup

    @staticmethod
    def find(pair):
        setup = Session().query(Trade).filter_by(pair=pair).first()
        return setup

    def __repr__(self):
        return "<Trade(nonce='%s', pair='%s', signal='%s')>" % (
                                self.nonce, self.pair, self.signal)


Base.metadata.create_all(engine)
