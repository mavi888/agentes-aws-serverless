# Demo - Herramientas pre-construidas

import logging

from strands import Agent
from strands_tools import current_time, http_request

# Activar debug logging de Strands
logging.getLogger("strands").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

agent = Agent(
    system_prompt="You are a helpful assistant...",
    tools=[current_time, http_request]
)

agent("""
1. What is the current time in UTC?
2. Search Wikipedia for Big O notation
""")


