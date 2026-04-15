from strands import Agent

agent = Agent()

# Ask the agent a question that uses the available tools
message = """
Can you name the 4 biggest cities of uruguay?
"""
agent(message)