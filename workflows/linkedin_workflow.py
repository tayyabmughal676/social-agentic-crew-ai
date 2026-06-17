import os
import logging
import asyncio
from typing import Dict, Any
from crewai import Crew, Task, LLM, Process

from agents.research_agent import ResearchAgent
from agents.writer_agent import WriterAgent
from agents.publisher_agent import PublisherAgent
from utils.llm_setup import get_llm

logger = logging.getLogger(__name__)

class LinkedInPostWorkflow:
    def __init__(self):
        self.default_llm = get_llm()
        
        self.research_agent = ResearchAgent().create_agent()
        self.writer_agent = WriterAgent().create_agent()
        self.publisher_agent = PublisherAgent().create_agent()

        self.agents = [self.research_agent, self.writer_agent, self.publisher_agent]

    def create_tasks(self, topic: str, audience: str = "Professionals") -> list:
        # Task 1: Research & Strategy
        research_task = Task(
            description=f"""Deeply research the latest trends for '{topic}' targeting {audience}.
            Requirements:
            1. Find 3-5 trending keywords.
            2. Suggest 2 specific best posting times (with timezones).
            3. Provide a brief (2-3 sentence) strategic rationale for these choices.""",
            agent=self.research_agent,
            expected_output="Detailed strategy report including Keywords, Timing, and Rationale."
        )

        # Task 2: Content Production
        writing_task = Task(
            description=f"""Using the research provided, draft a complete and compelling LinkedIn post for '{topic}'.
            Target Audience: {audience}
            
            Structure:
            1. Powerful Hook (first 2 lines).
            2. Value Body (detailed paragraphs with clear spacing).
            3. 3-5 Strategic hashtags.
            4. Strong Call-to-Action.
            
            IMPORTANT: Ensure the post is fully finished and doesn't cut off. Do not use markdown headers (###).""",
            agent=self.writer_agent,
            expected_output="A complete, professional LinkedIn post ready for direct publication.",
            context=[research_task]
        )

        # Task 3: Professional Documentation
        publishing_task = Task(
            description=f"""Aggregate the strategy and the final post into a professional Content Blueprint PDF.
            
            Topic: '{topic}'
            
            Action: Use the PDF Generator Tool.
            Inputs for Tool:
            - 'content': The COMPLETE post from the writer.
            - 'topic': '{topic}'
            - 'strategy_summary': The keywords and timing strategy from the analyst.""",
            agent=self.publisher_agent,
            expected_output="File path to the generated Blueprint PDF.",
            context=[research_task, writing_task]
        )

        return [research_task, writing_task, publishing_task]

    async def _execute_crew(self, crew: Crew) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, crew.kickoff)

    async def run_workflow(self, topic: str, audience: str = "Professionals", task_callback: Any = None) -> Dict[str, Any]:
        try:
            logger.info(f"Starting optimized workflow for topic: {topic}")
            tasks = self.create_tasks(topic, audience)
            
            crew = Crew(
                agents=self.agents,
                tasks=tasks,
                verbose=True,
                process=Process.sequential,
                manager_llm=self.default_llm,
                task_callback=task_callback,
                memory=False
            )
            
            result = await self._execute_crew(crew)
            return {
                "status": "success",
                "topic": topic,
                "result": str(result),
                "message": "Professional content blueprint generated successfully"
            }
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            return {"status": "error", "topic": topic, "error": str(e)}
