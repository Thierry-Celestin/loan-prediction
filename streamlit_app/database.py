
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker

url = "postgresql+psycopg2://postgres:root@localhost:8000/LoanPrediction"

engine = create_engine(url)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Loan(Base):
    __tablename__ = 'loan_prediction'

    id = Column(Integer, primary_key=True,autoincrement=True)
    created_date = Column(Date, default=func.current_date())
    created_time = Column(Time, default=func.current_time())
    source = Column(String)
    dependants = Column(Integer)
    education = Column(String)
    employment = Column(String)
    annual_income = Column(Integer)
    loan_amount = Column(Integer)
    loan_term = Column(Integer)
    cibil_score = Column(Integer)
    result = Column(String)


Base.metadata.create_all(engine)
