from agents.agents import billing_agent
from tasks.tasks import run_billing_crew
from crewai import Crew, Process


def run_billing_question(question: str, email: str) -> str:
    """Called by POST /question."""
    task = run_billing_crew(question, email)
    crew = Crew(
        agents=[billing_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
    return str(crew.kickoff())