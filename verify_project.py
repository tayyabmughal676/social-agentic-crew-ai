import time
import requests
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def run_test():
    print("🚀 Starting End-to-End Project Test...")
    
    # 1. Health Check
    try:
        health = requests.get("http://127.0.0.1:8000/health")
        print(f"✅ Server Health: {health.json()}")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return

    # 2. LM Studio Reachability Check (optional but good)
    # Actually, we'll let the agent fail if it can't reach it.

    # 3. Create Posting Workflow
    payload = {
        "topic": "Agentic Workflows are the future of AI and Businesses",
        "urgency": "normal",
        "target_audience": "Businessmen",
        "tone": "professional",
        "include_hashtags": True,
        "post_length": "short"
    }
    
    print(f"📝 Creating post workflow for topic: {payload['topic']}")
    resp = requests.post(f"{BASE_URL}/create-post", json=payload)
    if resp.status_code != 200:
        print(f"❌ Failed to create post: {resp.text}")
        return
    
    data = resp.json()
    workflow_id = data.get("workflow_id")
    print(f"✅ Workflow Created! ID: {workflow_id}")

    # 4. Polling Status
    print(f"⏳ Polling status (waiting for approval stage)...")
    max_retries = 100
    for i in range(max_retries):
        status_resp = requests.get(f"{BASE_URL}/workflow/{workflow_id}")
        status_data = status_resp.json()
        status = status_data.get("status")
        step = status_data.get("current_step")
        
        print(f"[{i+1}/{max_retries}] Status: {status} | Step: {step}")
        
        if status == "awaiting_approval":
            print("\n🎉 Workflow is Awaiting Approval!")
            result_content = status_data.get('result') or ""
            print(f"Content Preview: {result_content[:100]}...")
            
            # 5. Approve Workflow
            print("👍 Approving workflow...")
            approve_resp = requests.post(
                f"{BASE_URL}/workflow/{workflow_id}/approve", 
                json={
                    "workflow_id": workflow_id,
                    "action": "approve"
                }
            )
            print(f"Approval Response: {approve_resp.json()}")
            
            # Check final status
            final_resp = requests.get(f"{BASE_URL}/workflow/{workflow_id}")
            print(f"🏆 Final Status: {final_resp.json().get('status')}")
            return
            
        if status == "error":
            print(f"❌ Workflow failed with error: {status_data.get('error_details')}")
            return
            
        time.sleep(5) # Reduced poll time to 5 seconds for speed

    print("❌ Test timed out before reaching approval stage.")

if __name__ == "__main__":
    run_test()
