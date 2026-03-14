from sqlalchemy import Column, ForeignKey, Integer, String, Text
from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(50))
    address = Column(Text(255))

class PersonBillingDetailsDb(Base):
    __tablename__ = "person_billing_details"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100))

    # One person can have many billing records
    billings = relationship("BillingDetailsDb", back_populates="person", cascade="all, delete-orphan")


class BillingDetailsDb(Base):
    __tablename__ = "billing_details"

    id = Column(Integer, primary_key=True, index=True)
    billed_with = Column(String(100))
    actual_demand_kw = Column(String(100))
    billed_demand_kw = Column(String(100))
    basic_customer_charge = Column(String(100))
    energy_charge = Column(String(100))
    customer_assistance_recovery = Column(String(100))
    clean_energy_rider = Column(String(100))
    storm_recovery_charge = Column(String(100))
    summary_of_rider_adjustments = Column(String(100))
    sales_tax = Column(String(100))
    total_charge = Column(String(100))
    month = Column(String(20))

    person_id = Column(Integer, ForeignKey("person_billing_details.id"))
    person = relationship("PersonBillingDetailsDb", back_populates="billings")