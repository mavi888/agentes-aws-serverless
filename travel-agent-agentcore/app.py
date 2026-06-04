#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.lambda_stack import LambdaStack
from stacks.agentcore_stack import AgentCoreStack


app = cdk.App()

# ── Stack 1: Lambda independiente para get_trip_summary ───────────────────────
lambda_stack = LambdaStack(app, "TravelAgentLambdaStack")

# ── Stack 2: AgentCore Memory + Gateway ───────────────────────────────────────
agent_stack = AgentCoreStack(
    app, 
    "TravelAssitant-AgentCoreStack",
    lambda_arn=lambda_stack.trip_summary_function.function_arn
)

app.synth()
