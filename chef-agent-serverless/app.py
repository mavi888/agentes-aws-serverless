#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.mcp_stack import McpStack
from stacks.agent_stack import AgentStack


app = cdk.App()

# Stack 1: Servidor MCP (llamar al servicio de MealDB)
mcp_stack = McpStack(app, "McpMeal1Stack")

# Stack 2: Agente chef (Strands + Telegram)
agent_stack = AgentStack(app, "Chef1AgentStack", mcp_endpoint=mcp_stack.mcp_endpoint)
agent_stack.add_dependency(mcp_stack)

app.synth()
