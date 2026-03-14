from datetime import timedelta
import io
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import asc, desc
from database import session, engine
import db_models 
from jwt_utils import create_access_token, get_current_user, require_role
import models
from password import hash_password, verify_password
from fastapi.responses import StreamingResponse
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt

app = FastAPI()

db_models.Base.metadata.create_all(bind=engine)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup")
def signup(person: models.PersonSignup, db=Depends(get_db)):
    person_in_db = db.query(db_models.Person).filter(db_models.Person.email == person.email).first()
    if person_in_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    password = hash_password(person.password)
    new_person = db_models.Person(email=person.email, password=password, role=person.role, address=person.address)
    db.add(new_person)
    db.commit()
    return {"message": "Person signed up successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    person_in_db = db.query(db_models.Person).filter(db_models.Person.email == form_data.username).first()
    if not person_in_db or not verify_password(person_in_db.password, form_data.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"username": form_data.username, "role": person_in_db.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/user")
def get_user(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

@app.post("/billing")
def billing(details: models.PersonBillingDetails, current_user: str = Depends(require_role("admin")), db=Depends(get_db)):
    person_in_db = db.query(db_models.Person).filter(db_models.Person.email == details.email).first()
    if not person_in_db:
        raise HTTPException(status_code=404, detail="Person not found")

    billing_details_db = db_models.BillingDetailsDb(
        billed_with=details.billing_details.billed_with,   
        actual_demand_kw=details.billing_details.actual_demand_kw,
        billed_demand_kw=details.billing_details.billed_demand_kw,
        basic_customer_charge=details.billing_details.basic_customer_charge,
        energy_charge=details.billing_details.billed_with * 0.15,
        customer_assistance_recovery=details.billing_details.customer_assistance_recovery,
        clean_energy_rider=details.billing_details.clean_energy_rider,
        storm_recovery_charge=details.billing_details.storm_recovery_charge,
        summary_of_rider_adjustments=details.billing_details.summary_of_rider_adjustments,
        sales_tax=details.billing_details.billed_with * 0.07,
        month=details.billing_details.month
    )
    total_charge=details.billing_details.basic_customer_charge + billing_details_db.energy_charge
    + details.billing_details.customer_assistance_recovery + details.billing_details.clean_energy_rider
    + details.billing_details.storm_recovery_charge + details.billing_details.summary_of_rider_adjustments
    + billing_details_db.sales_tax
    billing_details_db.total_charge = total_charge
    person_billing_details = db_models.PersonBillingDetailsDb(email=details.email)
    person_billing_details.billings.append(billing_details_db)
    db.add(person_billing_details)
    db.commit()
    db.refresh(person_billing_details)
    db.refresh(billing_details_db)
    return {"person_billing_details": person_billing_details,
            "billing_details": billing_details_db}

@app.get("/billing")
def get_billing_details(current_user: str = Depends(require_role("user")), db=Depends(get_db)):
    result = db.query(db_models.BillingDetailsDb, db_models.PersonBillingDetailsDb)\
    .join(db_models.PersonBillingDetailsDb)\
    .filter(db_models.PersonBillingDetailsDb.email == current_user.get("username"))\
    .order_by(desc(db_models.BillingDetailsDb.month))\
    .first()

    if not result:
        raise HTTPException(status_code=404, detail="Person not found")
    
    bill, person = result

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Email: {person.email}", styles["Title"]))
    elements.append(Spacer(1, 12))


    data = [
        ["Month", bill.month],
        ["Billed With", bill.billed_with],
        ["Actual Demand (kW)", bill.actual_demand_kw],
        ["Billed Demand (kW)", bill.billed_demand_kw],
        ["Basic Customer Charge", bill.basic_customer_charge],
        ["Energy Charge", bill.energy_charge],
        ["Customer Assistance Recovery", bill.customer_assistance_recovery],
        ["Clean Energy Rider", bill.clean_energy_rider],
        ["Storm Recovery Charge", bill.storm_recovery_charge],
        ["Summary of Rider Adjustments", bill.summary_of_rider_adjustments],
        ["Sales Tax", bill.sales_tax],
        ["Total", bill.total_charge],
    ]

    actual = float(bill.actual_demand_kw)
    billed = float(bill.billed_demand_kw)

    if actual < billed:
        warning = f"Warning: You are billed for {billed} kW but only used {actual} kW."
    else:
        warning = "Demand usage is within billed capacity."

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
    ]))

    elements.append(Spacer(1, 20))
    elements.append(table)
    elements.append(Paragraph(warning, styles["Heading3"]))
    elements.append(Spacer(1, 20))


    bills = db.query(db_models.BillingDetailsDb)\
    .join(db_models.PersonBillingDetailsDb)\
    .filter(db_models.PersonBillingDetailsDb.email == current_user.get("username"))\
    .order_by(asc(db_models.BillingDetailsDb.month))\
    .limit(6)\
    .all()
    months = [b.month for b in bills]
    totals = [float(b.total_charge) for b in bills]

    plt.figure()
    plt.plot(months, totals, marker="o")
    plt.xlabel("Month")
    plt.ylabel("Total Bill")
    plt.title("Last Months Billing Comparison")

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)

    graph = Image(img_buffer, width=400, height=250)
    elements.append(graph)

    doc.build(elements)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=my_billings.pdf"}
    )