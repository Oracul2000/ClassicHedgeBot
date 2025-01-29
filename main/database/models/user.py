from sqlalchemy import MetaData, Table, String, Integer, Column, Text, DateTime, Boolean, ForeignKey, Date, Double
from sqlalchemy.orm import declarative_base, relationship
from database.models.base import Base
# from models.base import Base


class API(Base):
    __tablename__ = 'API'

    id = Column(Integer, nullable=True, unique=True,
                primary_key=True, autoincrement=True)
    name = Column(String(), nullable=True)
    bybitapi = Column(String(), nullable=True)
    bybitsecret = Column(String(), nullable=True)
    bingxapi = Column(String(), nullable=True)
    bingxsecret = Column(String(), nullable=True)
    symbol = Column(String(), nullable=True)
    deposit = Column(Double(), nullable=True)
    user_id = Column(Integer, ForeignKey("User.id"))
    user = relationship("User", back_populates="apis")
    pid = Column(String(), nullable=True)
    max_loss = Column(Double(), nullable=True)


class User(Base):
    __tablename__ = 'User'
    id = Column(Integer, nullable=True, unique=True,
                primary_key=True, autoincrement=True)
    name = Column(String(), nullable=True)
    apis = relationship("API", back_populates="user")
