"""CrewAI integration example - boundary-aware crew execution."""

import sys
sys.path.insert(0, "/path/to/agent-wellbeing-kit")

from quiet_hours import should_send_message
from crewai import Crew, Agent, Task

def run_crew_with_boundaries(crew: Crew):
    result = crew.kickoff()

    if should_send_message(tag="crew-output"):
        print(f"Crew result: {result}")
    else:
        with open("/tmp/crew-result.txt", "w") as f:
            f.write(str(result))
        print("Crew finished. Result saved to /tmp/crew-result.txt (quiet hours).")

    return result
