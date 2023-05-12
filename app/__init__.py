import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename='icarusbot.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.addHandler(logging.StreamHandler())

Base = declarative_base()
engine = create_engine('sqlite:///trades.db', echo=False)
Session = sessionmaker(bind=engine)
db = Session()
