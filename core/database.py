from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///database/positions.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)  # 👈 Добавляем это!
    symbol = Column(String)
    entry_price = Column(Float)
    amount = Column(Float)
    take_profit = Column(Float)
    stop_loss = Column(Float)
    direction = Column(String) 

class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    balance = Column(Float)

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    pnl = Column(Float)

Base.metadata.create_all(engine)
