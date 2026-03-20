from datetime import date

from pydantic import BaseModel


class BillingDetails(BaseModel):
    billed_with: float
    actual_demand_kw: float
    billed_demand_kw: float
    basic_customer_charge: float
    customer_assistance_recovery: float
    clean_energy_rider: float
    storm_recovery_charge: float
    summary_of_rider_adjustments: float
    month: date

class PersonBillingDetails(BaseModel):
    email: str
    billing_details: BillingDetails

class PersonSignup(BaseModel):
    email: str
    password: str
    role: str
    address: str

class QuestionRequest(BaseModel):
    question: str


