from crewai.tools import tool
from sqlalchemy.orm import Session
from database import session 
from db_models import Person, PersonBillingDetailsDb, BillingDetailsDb
import json

def get_db_session() -> Session:
    return session()
 
 
@tool("CurrentBill")
def get_current_bill(email: str) -> str:
    """
    Fetches the most recent (current) bill for a customer by email.
    Returns billing details for the latest month on record.
    """
    db = get_db_session()
    try:
        person_billing = (
            db.query(PersonBillingDetailsDb)
            .filter(PersonBillingDetailsDb.email == email)
            .first()
        )
        if not person_billing:
            return json.dumps({"error": f"No billing account found for {email}"})
 
        latest_bill = (
            db.query(BillingDetailsDb)
            .filter(BillingDetailsDb.person_id == person_billing.id)
            .order_by(BillingDetailsDb.id.desc())
            .first()
        )
        if not latest_bill:
            return json.dumps({"error": "No bills found for this customer"})
 
        return json.dumps({
            "month": latest_bill.month.isoformat(),
            "billed_with": latest_bill.billed_with,
            "actual_demand_kw": latest_bill.actual_demand_kw,
            "billed_demand_kw": latest_bill.billed_demand_kw,
            "basic_customer_charge": latest_bill.basic_customer_charge,
            "energy_charge": latest_bill.energy_charge,
            "customer_assistance_recovery": latest_bill.customer_assistance_recovery,
            "clean_energy_rider": latest_bill.clean_energy_rider,
            "storm_recovery_charge": latest_bill.storm_recovery_charge,
            "summary_of_rider_adjustments": latest_bill.summary_of_rider_adjustments,
            "sales_tax": latest_bill.sales_tax,
            "total_charge": latest_bill.total_charge,
        })
    finally:
        db.close()
 
 
@tool("BillHistory")
def get_bill_history(email: str) -> str:
    """
    Retrieves the full billing history for a customer by email.
    Returns a list of all past bills ordered from newest to oldest.
    """
    db = get_db_session()
    try:
        person_billing = (
            db.query(PersonBillingDetailsDb)
            .filter(PersonBillingDetailsDb.email == email)
            .first()
        )
        if not person_billing:
            return json.dumps({"error": f"No billing account found for {email}"})
 
        bills = (
            db.query(BillingDetailsDb)
            .filter(BillingDetailsDb.person_id == person_billing.id)
            .order_by(BillingDetailsDb.id.desc())
            .all()
        )
        if not bills:
            return json.dumps({"bills": [], "message": "No billing history found"})
 
        history = [
            {
                "month": b.month.isoformat(),
                "billed_with": b.billed_with,
                "actual_demand_kw": b.actual_demand_kw,
                "billed_demand_kw": b.billed_demand_kw,
                "basic_customer_charge": b.basic_customer_charge,
                "energy_charge": b.energy_charge,
                "customer_assistance_recovery": b.customer_assistance_recovery,
                "clean_energy_rider": b.clean_energy_rider,
                "storm_recovery_charge": b.storm_recovery_charge,
                "summary_of_rider_adjustments": b.summary_of_rider_adjustments,
                "sales_tax": b.sales_tax,
                "total_charge": b.total_charge,
            }
            for b in bills
        ]
        return json.dumps({"email": email, "total_bills": len(history), "bills": history})
    finally:
        db.close()
 
 
@tool("ChargeDetail")
def get_charge_detail(email: str, month: str) -> str:
    """
    Provides a detailed breakdown of all charges for a specific billing month.
    Input: email and month (e.g. '2024-01')
    """
    db = get_db_session()
    try:
        person_billing = (
            db.query(PersonBillingDetailsDb)
            .filter(PersonBillingDetailsDb.email == email)
            .first()
        )
        if not person_billing:
            return json.dumps({"error": f"No billing account found for {email}"})
 
        bill = (
            db.query(BillingDetailsDb)
            .filter(
                BillingDetailsDb.person_id == person_billing.id,
                BillingDetailsDb.month == month,
            )
            .first()
        )
        if not bill:
            return json.dumps({"error": f"No bill found for {email} in {month}"})
 
        return json.dumps({
            "month": bill.month.isoformat(),
            "breakdown": {
                "basic_customer_charge": bill.basic_customer_charge,
                "energy_charge": bill.energy_charge,
                "customer_assistance_recovery": bill.customer_assistance_recovery,
                "clean_energy_rider": bill.clean_energy_rider,
                "storm_recovery_charge": bill.storm_recovery_charge,
                "summary_of_rider_adjustments": bill.summary_of_rider_adjustments,
                "sales_tax": bill.sales_tax,
            },
            "demand": {
                "actual_demand_kw": bill.actual_demand_kw,
                "billed_demand_kw": bill.billed_demand_kw,
                "billed_with": bill.billed_with,
            },
            "total_charge": bill.total_charge,
        })
    finally:
        db.close()
 
 
@tool("ProfileInfo")
def get_profile_info(email: str) -> str:
    """
    Retrieves customer profile information (email, address, role).
    Use this to personalize responses or verify customer identity context.
    """
    db = get_db_session()
    try:
        person = db.query(Person).filter(Person.email == email).first()
        if not person:
            return json.dumps({"error": f"No profile found for {email}"})
 
        return json.dumps({
            "email": person.email,
            "role": person.role,
            "address": person.address,
        })
    finally:
        db.close()