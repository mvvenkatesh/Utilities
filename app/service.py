import io
from fastapi.responses import StreamingResponse
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import app.db_models as db_models


def calculate_energy_charge(details):
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
    return billing_details_db

def create_pdf(result):
    bill = result

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Billing Report", styles["Title"]))
    elements.append(Paragraph(f"Email: {bill.person.email}", styles["Title"]))
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

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
    ]))

    elements.append(Spacer(1, 20))
    elements.append(table)

    bills = sorted(result.person.billings, key=lambda b: b.month)
    
    months = [b.month for b in bills]
    totals = [float(b.total_charge) for b in bills]
    indices = range(len(months))

    plt.figure()
    plt.plot(indices, totals, marker="o")  
    plt.xlabel("Month")
    plt.ylabel("Total Bill ($)")
    plt.title("Last Months Billing Comparison")
    plt.xticks(ticks=indices, labels=months, ha="right") 
    plt.tight_layout()

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