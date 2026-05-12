#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.mcp_stack import McpStack


app = cdk.App()
McpStack(app, "MCPStack01")

app.synth()
