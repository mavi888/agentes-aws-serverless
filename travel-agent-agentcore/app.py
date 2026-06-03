#!/usr/bin/env python3
import os

import aws_cdk as cdk

import AgentCoreStack from agentcore_stack


app = cdk.App()

AgentCoreStack=AgentCoreStack(app, "TravelAssitant-AgentCoreStack")    

app.synth()
