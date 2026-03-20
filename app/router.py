from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from app.crew_local import run_billing_question
from app.database import session
import app.db_models as db_models
from app.jwt_utils import create_access_token, get_current_user, require_role
import app.models as models
from app.password import hash_password, verify_password
from app.service import calculate_energy_charge, create_pdf

router = APIRouter()

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(person: models.PersonSignup, db=Depends(get_db)):
    person_in_db = db.query(db_models.Person).filter(db_models.Person.email == person.email).first()
    if person_in_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    password = hash_password(person.password)
    new_person = db_models.Person(email=person.email, password=password, role=person.role, address=person.address)
    db.add(new_person)
    db.commit()
    return {"message": "Person signed up successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    person_in_db = db.query(db_models.Person).filter(db_models.Person.email == form_data.username).first()
    if not person_in_db or not verify_password(person_in_db.password, form_data.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token_expires = timedelta(minutes=15)
    access_token = create_access_token(
        data={"username": form_data.username, "role": person_in_db.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/user")
def get_user(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

@router.post("/billing")
def billing(details: models.PersonBillingDetails, current_user: str = Depends(require_role("admin")), db=Depends(get_db)):
    person_in_db = db.query(db_models.Person).filter(db_models.Person.email == details.email).first()
    if not person_in_db:
        raise HTTPException(status_code=404, detail="Person not found")
    
    person_billing_details = db.query(db_models.PersonBillingDetailsDb)\
    .filter(db_models.PersonBillingDetailsDb.email == details.email)\
    .first()

    if not person_billing_details:
        person_billing_details = db_models.PersonBillingDetailsDb(email=details.email)
        db.add(person_billing_details)
        db.commit()
        db.refresh(person_billing_details)

    billing_details_db = calculate_energy_charge(details)
    billing_details_db.person_id = person_billing_details.id
    
    db.add(billing_details_db)
    db.commit()
    db.refresh(billing_details_db)
    db.refresh(person_billing_details)
    return {"person_billing_details": person_billing_details,
            "billing_details": billing_details_db}

@router.get("/billing")
def get_billing_details(current_user: str = Depends(require_role("user")), db=Depends(get_db)):
    result = db.query(db_models.BillingDetailsDb)\
    .options(
        selectinload(db_models.BillingDetailsDb.person)
        .selectinload(db_models.PersonBillingDetailsDb.billings)
    )\
    .join(db_models.PersonBillingDetailsDb)\
    .filter(db_models.PersonBillingDetailsDb.email == current_user.get("username"))\
    .order_by(desc(db_models.BillingDetailsDb.month))\
    .first()

    if not result:
        raise HTTPException(status_code=404, detail="Person not found")
    
    return create_pdf(result)

@router.post("/question")
def ask_billing_question(body: models.QuestionRequest, current_user: str = Depends(require_role("user"))):
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
 
    answer = run_billing_question(body.question, current_user.get("username"))
    return {"question": body.question, "answer": answer}


