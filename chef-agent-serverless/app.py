#!/usr/bin/env python3
import os

import aws_cdk as cdk
from stacks.mcp_stack import McpStack
from stacks.agent_stack import AgentStack
from stacks.guardrails_stack import GuardrailStack
from stacks.knowledgebase_stack import KnowledgeBaseStack


app = cdk.App()

# Stack 1: Servidor MCP (llamar al servicio de MealDB)
mcp_stack = McpStack(app, "McpMeal1Stack")

# Stack 2: Guardrail stack
guardrail_stack = GuardrailStack(app, "ChefAgent1GuardrailStack")


# Stack 3: Knowledge base - Recetas de la abuela
kb = KnowledgeBaseStack(app, "ChefAgent1KnowledgeBaseStack")


# Stack 4: Agente chef (Strands + Telegram)
agent_stack = AgentStack(app, "Chef1AgentStack", 
    mcp_endpoint=mcp_stack.mcp_endpoint,
    guardrail_id=guardrail_stack.guardrail_id, 
    guardrail_version="1",
    kb_id=kb.knowledge_base_id,
    kb_arn=kb.knowledge_base_arn,
)

app.synth()
