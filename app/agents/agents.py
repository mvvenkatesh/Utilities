import os

from crewai import LLM, Agent
from dotenv import load_dotenv

from app.tools.tools import get_bill_history, get_charge_detail, get_current_bill, get_profile_info

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=300
)

billing_agent = Agent(
    role="Electricity Billing Assistant",
    goal=(
        "Help customers understand their electricity bills, charges, and account history. "
        "Answer questions accurately using the available tools to retrieve real billing data."
    ),
    backstory=(
        "You are an expert billing support agent for an electricity provider. "
        "You have access to customer billing data and can explain charges clearly. "
        "You always fetch data before answering — never guess. "
        "Be concise, friendly, and precise."
    ),
    tools=[
        get_current_bill,
        get_bill_history,
        get_charge_detail,
        get_profile_info,
    ],
    llm=llm,
    verbose=True,
    allow_delegation=False,
)