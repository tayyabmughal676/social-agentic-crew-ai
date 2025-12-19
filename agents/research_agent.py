from crewai import Agent
from crewai_tools import SerperDevTool
from utils.llm_setup import get_llm

class ResearchAgent:
    def __init__(self):
        self.llm = get_llm()
        self.search_tool = SerperDevTool()

    def create_agent(self):
        return Agent(
            role="Market Analyst",
            goal="Research trends and define the best LinkedIn strategy (keywords & timing).",
            backstory="Experienced analyst who finds high-value insights and optimal engagement windows.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[self.search_tool],
            max_iter=2,
            memory=False
        )
