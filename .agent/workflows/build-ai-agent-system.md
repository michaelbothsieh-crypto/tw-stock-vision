---
description: Workflow to design, implement, and evaluate a production-ready AI agent.
---

1. **Define use case and reliability targets**
   - Goal: Choose a narrow use case and measurable quality goals.
   - Notes: Set latency, quality, and failure-rate thresholds before implementation.
   - Recommended Skills: ai-agents-architect, agent-evaluation, product-manager-toolkit

2. **Design architecture and retrieval**
   - Goal: Design tools, memory, and retrieval strategy for the agent.
   - Notes: Keep retrieval quality measurable and version prompt/tool contracts.
   - Recommended Skills: llm-app-patterns, rag-implementation, vector-database-engineer, embedding-strategies

3. **Implement orchestration**
   - Goal: Implement the orchestration loop and production safeguards.
   - Notes: Start with constrained tool permissions and explicit fallback behavior.
   - Recommended Skills: langgraph, mcp-builder, workflow-automation

4. **Evaluate and iterate**
   - Goal: Run benchmark scenarios and improve weak areas systematically.
   - Notes: Use test datasets and failure buckets to guide each iteration cycle.
   - Recommended Skills: agent-evaluation, langfuse, kaizen
