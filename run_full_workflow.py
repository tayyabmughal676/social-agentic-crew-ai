import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.linkedin_workflow import LinkedInPostWorkflow
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("🚀 Starting LinkedIn Post Workflow...")
    topic = "The Future of AI Agents in 2026"
    print(f"📝 Topic: {topic}\n")
    
    workflow = LinkedInPostWorkflow()
    
    try:
        # Run the workflow
        result = await workflow.run_workflow(topic)
        
        if result["status"] == "success":
            print("\n✅ Workflow Completed Successfully!")
            print("-" * 50)
            print(f"Topic: {result['topic']}")
            print("-" * 50)
            
            # Check for generated PDF in the new location
            from datetime import datetime
            import re
            output_dir = "storage/pdfs"
            date_str = datetime.now().strftime("%Y-%m-%d")
            safe_topic = re.sub(r'[^\w\-]', '', re.sub(r'[\s]+', '-', topic.strip()))
            expected_filename = f"{date_str}-{safe_topic}.pdf"
            expected_path = os.path.join(output_dir, expected_filename)
            
            if os.path.exists(expected_path):
                print(f"\n📄 Professional PDF Generated: {expected_path}")
            else:
                print(f"\n⚠️ Warning: PDF was expected at {expected_path} but not found.")
                if os.path.exists(output_dir):
                    print(f"Files in {output_dir}: {os.listdir(output_dir)}")
        else:
            print(f"\n❌ Workflow Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
