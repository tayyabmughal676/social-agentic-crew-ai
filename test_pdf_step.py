import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.publisher_agent import PublisherAgent
from crewai import Task, Crew

async def test_only_pdf_step():
    print("🎯 Testing Professional PDF Step...")
    topic = "AI Productivity 2026"
    content = "This is a pre-generated post for testing professional PDF creation.\n\nKey takeaways:\n1. Efficiency\n2. Speed\n3. Quality"
    strategy = "Keywords: AI, Tech, Future. Posting Tuesday at 10 AM."
    
    agent_factory = PublisherAgent()
    agent = agent_factory.create_agent()
    
    publish_task = Task(
        description=f"Generate a professional PDF content blueprint for: '{topic}'. Use content: {content} and strategy: {strategy}",
        agent=agent,
        expected_output="Path to the generated PDF."
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[publish_task],
        verbose=True
    )
    
    print("🎬 Kicking off the Operations Manager...")
    result = await asyncio.get_event_loop().run_in_executor(None, crew.kickoff)
    print("\n✅ Crew finished!")
    
    # Verify file
    date_str = datetime.now().strftime("%Y-%m-%d")
    import re
    safe_topic = re.sub(r'[^\w\-]', '', re.sub(r'[\s]+', '-', topic.strip()))
    expected_filename = f"{date_str}-{safe_topic}.pdf"
    expected_path = os.path.join("storage/pdfs", expected_filename)
    
    if os.path.exists(expected_path):
        print(f"🎉 SUCCESS! PDF generated at: {expected_path}")
    else:
        print(f"❌ FAILED! Expected {expected_path}")
        if os.path.exists("storage/pdfs"):
            print(f"Actual files: {os.listdir('storage/pdfs')}")

if __name__ == "__main__":
    asyncio.run(test_only_pdf_step())
