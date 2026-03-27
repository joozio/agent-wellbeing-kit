"""LangChain integration example - check boundaries before agent output."""

import sys
sys.path.insert(0, "/path/to/agent-wellbeing-kit")

from quiet_hours import should_send_message
from langchain.agents import AgentExecutor

def run_agent_with_boundaries(agent_executor, query):
    result = agent_executor.invoke({"input": query})

    if should_send_message(tag="agent-output"):
        print(result["output"])
    else:
        print("Result saved but notification suppressed (quiet hours).")

    return result
