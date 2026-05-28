#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.mcp_stack import McpStack
from stacks.agent_stack import AgentStack
from stacks.guardrails_stack import GuardrailStack
from stacks.knowledgebase_stack import KnowledgeBaseStack


app = cdk.App()

# Stack 1: Servidor MCP (base de conocimiento interna)
mcp_stack = McpStack(app, "MCPStack01")

# Stack 2: Guardrail stack
guardrail_stack = GuardrailStack(app, "AgenteSoporteGuardrail01Stack")

# Stack 3: Knowledge Base Stack
kb = KnowledgeBaseStack(app, "SupportAgentKnowledgeBaseStack")

# Stack 4: Agente de soporte
AgentStack(app, "AgentStack01", 
    guardrail_id=guardrail_stack.guardrail_id, 
    guardrail_version="2",
    kb_id=kb.knowledge_base_id,
    kb_arn=kb.knowledge_base_arn,
)

app.synth()
