from crewai import Task
from agents.agents import billing_agent

def run_billing_crew(question: str, email: str) -> str:
    task = Task(
        description=(
            f"Customer email: {email}\n"
            f"Customer question: {question}\n\n"
            "Use the appropriate tools to retrieve the customer's billing data "
            "and provide a clear, accurate answer. Always pass the customer's email "
            "when calling tools."
        ),
        expected_output=(
            "1. Provide a clear answer to the customer's billing question.\n"
            "2. Include relevant billing details such as month, charges, or demand values.\n"
            "3. Use accurate data retrieved from the customer's account.\n"
            "4. Respond in a friendly and easy-to-understand manner."
        ),
        agent=billing_agent,
    )
    return task