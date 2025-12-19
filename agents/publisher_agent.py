from crewai import Agent
from utils.llm_setup import get_llm
from tools.pdf_generator import PDFGeneratorTool

class PublisherAgent:
    def __init__(self):
        self.llm = get_llm()

    def create_agent(self):
        return Agent(
            role="Operations Manager",
            goal="Package the final content into a high-end, client-ready PDF document.",
            backstory="""You are an expert in document design and operational excellence. 
            Your job is to take the final post and any strategic insights and turn them into 
            a professional 'Content Blueprint' PDF that looks manually designed.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            max_iter=2,
            memory=False,
            tools=[PDFGeneratorTool()]
        )
