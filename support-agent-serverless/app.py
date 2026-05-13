#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.mcp_stack import McpStack
from stacks.agent_stack import AgentStack


app = cdk.App()
mcp_stack = McpStack(app, "MCPStack01")

AgentStack(app, "AgentStack01", mcp_endpoint=mcp_stack.mcp_endpoint)

app.synth()
