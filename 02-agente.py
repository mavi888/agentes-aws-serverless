# Demo - Herramientas @tool

from strands import Agent, tool

@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word: The input word to search in
        letter: The specific letter to count

    Returns:
        The number of occurrences of the letter
    """
    return word.lower().count(letter.lower())

agent = Agent(tools=[letter_counter])

agent("How many R's are in strawberry?")