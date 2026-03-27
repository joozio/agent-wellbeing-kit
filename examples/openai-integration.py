"""OpenAI API integration example - respect quiet hours for notifications."""

import sys
sys.path.insert(0, "/path/to/agent-wellbeing-kit")

from quiet_hours import should_send_message
from error_registry import check_errors

def call_with_boundaries(client, messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o", messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        # Feed errors to the registry
        check_errors([str(e)])
        raise

def notify_if_allowed(text, tag="agent-notification"):
    if should_send_message(tag=tag):
        print(f"[agent] {text}")
    else:
        print(f"[suppressed] {text}")
