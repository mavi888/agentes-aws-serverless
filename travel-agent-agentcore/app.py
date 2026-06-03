#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.agentcore_stack import AgentCoreStack


app = cdk.App()

agent_stack = AgentCoreStack(app, "TravelAssitant-AgentCoreStack")

app.synth()
