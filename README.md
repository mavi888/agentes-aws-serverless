# Curso de Agentes de IA con AWS

_Infrastructure as code framework used_: AWS CDK
_AWS Services used_: Amazon Bedrock, AWS Lambda, Amazon Bedrock AgentCore, Strands, and many others

## Summary of the demo

In this demo you will see:

- How to create Agents with Strands
- How to host Agents with AWS Lambda
- Using Amazon Bedrock, models, guardrails and knowledge bases
- Using Amazon Bedrock AgentCore components (Memory, gateway, identity, etc.)

This demo is part of 5+ hour course in Desplegando.cloud. 

Important: this application uses various AWS services and there are costs associated with these services after the Free Tier usage - please see the AWS Pricing page for details. You are responsible for any AWS costs incurred. No warranty is implied in this example.


## Deploy this demo

Deploy the project to the cloud:

```
cdk synth
cdk deploy
```

When asked about functions that may not have authorization defined, answer (y)es. The access to those functions will be open to anyone, so keep the app deployed only for the time you need this demo running.

To delete the app:

```
cdk destroy
```