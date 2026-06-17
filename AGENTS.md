# CrewAI Agent Registry

This document lists the specialized agents deployed in the LinkedIn Post Writer workflow. Each agent operates with unique roles, backstories, tools, and objectives to construct professional LinkedIn Content Blueprints.

---

## 🔍 1. Market Analyst (Research Agent)
* **Python Module**: [research_agent.py](file:///Users/mac/Desktop/n8n/social-agentic-crew-ai/agents/research_agent.py)
* **Role**: `Market Analyst`
* **Goal**: Research trends and define the best LinkedIn strategy (keywords & timing).
* **Backstory**: An experienced analyst who finds high-value insights and identifies optimal engagement windows.
* **Tools**: 
  * `SerperDevTool` (Google Search API integration)
* **Configuration**:
  * `max_iter`: 2
  * `allow_delegation`: `False`
  * `memory`: `False`

---

## ✍️ 2. Executive LinkedIn Copywriter (Writer Agent)
* **Python Module**: [writer_agent.py](file:///Users/mac/Desktop/n8n/social-agentic-crew-ai/agents/writer_agent.py)
* **Role**: `Executive LinkedIn Copywriter`
* **Goal**: Draft high-impact, full-length LinkedIn posts with a clear hook and conclusion.
* **Backstory**: Elite ghostwriter for tech executives. Specializes in storytelling and ensuring every post is complete, engaging, and ready for thousands of views without cutting off thoughts mid-sentence.
* **Tools**: None (uses contextual output from the Market Analyst).
* **Configuration**:
  * `max_iter`: 2
  * `allow_delegation`: `False`
  * `memory`: `False`

---

## 📋 3. Operations Manager (Publisher Agent)
* **Python Module**: [publisher_agent.py](file:///Users/mac/Desktop/n8n/social-agentic-crew-ai/agents/publisher_agent.py)
* **Role**: `Operations Manager`
* **Goal**: Package the final content into a high-end, client-ready PDF document.
* **Backstory**: An expert in document design and operational excellence. Takes the final post and any strategic insights and converts them into a professional 'Content Blueprint' PDF that looks manually designed.
* **Tools**:
  * `PDFGeneratorTool` (custom document generator utility)
* **Configuration**:
  * `max_iter`: 2
  * `allow_delegation`: `False`
  * `memory`: `False`
