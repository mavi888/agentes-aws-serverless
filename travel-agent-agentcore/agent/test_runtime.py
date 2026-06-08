"""
Script para testear el AgentCore Runtime del Travel Agent.

Configuración antes de correr:
  1. Hacer cdk deploy --all en travel-agent-agentcore/
  2. Copiar el ARN del Runtime del output y setearlo como variable de entorno:

     export TRAVEL_AGENT_RUNTIME_ARN="arn:aws:bedrock-agentcore:us-east-1:<account>:runtime/TravelAgent1Runtime-XXXXXXXXXX"

  Podés encontrar el ARN en los outputs del cdk deploy (TravelAgent1RuntimeArn)
  o con:
     aws cloudformation describe-stacks --stack-name TravelAssistant1-AgentCoreStack \
       --query "Stacks[0].Outputs[?OutputKey=='TravelAgent1RuntimeArn'].OutputValue" \
       --output text

Uso (desde el directorio agent/):
    python3 test_runtime.py --actor manuela
    python3 test_runtime.py --actor manuela --prompt "Busca vuelos de EZE a NRT"
"""

import json
import uuid
import argparse
import os
import boto3
from botocore.config import Config

RUNTIME_ARN = os.environ.get("TRAVEL_AGENT_RUNTIME_ARN")
REGION      = os.environ.get("AWS_REGION", "us-east-1")

if not RUNTIME_ARN:
    raise ValueError(
        "Seteá la variable de entorno TRAVEL_AGENT_RUNTIME_ARN con el ARN del Runtime.\n"
        "Podés encontrarlo en los outputs del cdk deploy (TravelAgent1RuntimeArn)."
    )

client = boto3.client(
    "bedrock-agentcore",
    region_name=REGION,
    config=Config(read_timeout=120, retries={"max_attempts": 2}),
)


def invoke(prompt: str, actor_id: str, session_id: str) -> str:
    payload = json.dumps({
        "prompt":     prompt,
        "actor_id":   actor_id,
        "session_id": session_id,
    })
    response = client.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=payload,
    )
    body = response["response"].read()
    return json.loads(body).get("response", body.decode())


def chat(actor_id: str, single_prompt: str = None):
    # session_id necesita tener al menos 33 caracteres
    session_id = f"test-{actor_id}-{uuid.uuid4().hex}"

    print(f"\n{'='*60}")
    print(f"  Travel Agent Runtime — Test")
    print(f"  actor_id  : {actor_id}")
    print(f"  session_id: {session_id[:40]}...")
    print(f"  Escribí 'salir' para terminar")
    print(f"{'='*60}\n")

    if single_prompt:
        print(f"Vos: {single_prompt}")
        print("Agente:", invoke(single_prompt, actor_id, session_id))
        return

    while True:
        try:
            user_input = input("Vos: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n¡Hasta luego! ✈️")
            break

        if not user_input:
            continue
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("¡Hasta luego! ✈️")
            break

        try:
            print(f"Agente: {invoke(user_input, actor_id, session_id)}\n")
        except Exception as e:
            print(f"⚠️  Error: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor",  default="test-user")
    parser.add_argument("--prompt", default=None)
    args = parser.parse_args()
    chat(actor_id=args.actor, single_prompt=args.prompt)
