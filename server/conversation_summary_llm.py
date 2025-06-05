import os
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_conversation_summary(name: str, partner_name: str, history: list) -> str:
    """
    - Build instructions and input based on name, partner_name, and history.
    - Call OpenAI ChatCompletion to get a concise summary.
    - Return: "I talked with {partner_name} today: {summary_text}"
    """

    instructions = (
        f"You're {name}, one of the villagers in Stardew Valley. You just had a chat with another villager {partner_name}. "
        "Reflect on this conversation and summarize in one most important thought that is worth remembering about the person you met. "
        "Output only the thought. Remember, you're {name}."
    )

    # Join the history list into a single string (similar to JS `${history}`)
    # If history is a list of strings, join with newline or a delimiter.
    history_text = "\n".join(history) if isinstance(history, list) else str(history)

    input_text = (
        f"Here is the conversation you had: ---- {history_text} -----. \n\n"
        "Summarize it, be concise, but keep only the important things in full details. "
        "If any specific events/people mentioned, add those to the summary."
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": input_text},
        ]
    )

    summary_text = response.choices[0].message["content"].strip()
    return f"I talked with {partner_name} today: {summary_text}"
