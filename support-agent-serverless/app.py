#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.mcp_stack import McpStack
from stacks.agent_stack import AgentStack
from stacks.guardrails_stack import GuardrailStack


app = cdk.App()

# Stack 1: Servidor MCP (base de conocimiento interna)
mcp_stack = McpStack(app, "MCPStack01")

# Stack 2: Guardrail stack
guardrail_stack = GuardrailStack(app, "AgenteSoporteGuardrail01Stack")

# Stack 2: Agente de soporte (consume el MCP server)
AgentStack(app, "AgentStack01", 
    mcp_endpoint=mcp_stack.mcp_endpoint, 
    guardrail_id=guardrail_stack.guardrail_id,
    guardrail_version=guardrail_stack.guardrail_version_number
)

app.synth()
