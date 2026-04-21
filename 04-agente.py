from strands import Agent

agent = Agent(
    system_prompt="""You are a Computer Science Subject Expert specializing
    in explaining technical concepts clearly and concisely..."""
)

def interactive_session():
    print("CS Subject Expert (type 'exit' to quit)")
    print("----------------------------------------")
    
    while True:
        user_input = input("\nYour question: ")
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        
        print("\nThinking...\n")
        agent(user_input)

if __name__ == "__main__":
    interactive_session()