from crewai import Agent
from utils.llm_setup import get_llm

class WriterAgent:
    def __init__(self):
        self.llm = get_llm()

    def create_agent(self):
        return Agent(
            role="Executive LinkedIn Copywriter",
            goal="Draft high-impact, full-length LinkedIn posts with a clear hook and conclusion.",
            backstory="""Elite ghostwriter for tech executives. You specialize in storytelling 
            and ensuring every post is complete, engaging, and ready for a thousands of views. 
            You never cut off your thoughts mid-sentence.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=2,
            memory=False
        )
