import aws_cdk as core
import aws_cdk.assertions as assertions

from support_agent_serverless.support_agent_serverless_stack import SupportAgentServerlessStack

# example tests. To run these tests, uncomment this file along with the example
# resource in support_agent_serverless/support_agent_serverless_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = SupportAgentServerlessStack(app, "support-agent-serverless")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
