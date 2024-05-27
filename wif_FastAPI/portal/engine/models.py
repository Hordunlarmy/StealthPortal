from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

try:
    from StealthPortal.wif_FastAPI.portal.engine import Base
except ImportError:
    from portal.engine import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    messages = relationship('Message', backref='sender')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    key = Column(String(32), nullable=False)
    iv = Column(String(16), nullable=False)
    date_posted = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Message('{self.message}', '{self.key}', '{self.date_posted}')"
