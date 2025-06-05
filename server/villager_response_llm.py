import os
import openai

# Make sure you have OPENAI_API_KEY in your .env or environment
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_villager_reply(
    name: str,
    metadata: dict,
    partner_name: str,
    partner_metadata: dict,
    history: list,
    heard_message: str,
    relevant_memories=None,
) -> str:
    """
    Mirrors the logic from your JS version, using openai.ChatCompletion.create().
    """
    if relevant_memories is None:
        relevant_memories = {}

    # Build the “instructions” string
    instructions = [
        f"You live in Stardew Valley, you are a villager named {name}.",
        f"YOUR background: {metadata.get('background', '')}",
        "",
        f"You’re having a friendly conversation with {partner_name}.",
        f"Their background: {partner_metadata.get('background', '')}",
        "",
        metadata.get("goal", ""),
        "",
    ]

    # If relevant memories exist, include them
    if relevant_memories:
        # In your JS, you did: `Relevant memories from today that you want to use for conversation: - ${ relevantMemories.reply }`
        # Here, assume relevant_memories has a “reply” field or similar
        rm = relevant_memories.get("reply", "")
        instructions.append(f"Relevant memories from today that you want to use: - {rm}")
        instructions.append("")

    instructions += [
        "Your goal is to reply as " + name + ":",
        "- Keep it short, friendly, and in character, refer to what you learned today from others.",
        "- Avoid shallow small talk or formal conversation.",
        "- Only give a reply; no explanations or meta-comments.",
        "- Do not mention your own name; speak as the villager.",
        "- If conversation is ongoing, do not greet again.",
        "- Answer questions, ask clarifying questions, and evolve the topic."
    ]

    # Build the “input” string
    conversation_so_far = ["Conversation so far:"]
    for i, line in enumerate(history):
        conversation_so_far.append(f"{i+1}. {line}")
    conversation_so_far.append("")
    conversation_so_far.append(f'{partner_name} just said to you: "{heard_message}"')
    conversation_so_far.append("")
    conversation_so_far.append("Please respond. Answer questions, ask clarifying questions, and evolve the topic. Be concise, exchange short phrases:")

    # Concatenate them
    instruction_text = "\n".join(instructions)
    input_text = "\n".join(conversation_so_far)

    # Call OpenAI ChatCompletion (gpt-3.5-turbo)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": instruction_text},
            {"role": "user", "content": input_text},
        ],
        temperature=0.8,
        max_tokens=150,
    )

    # The “assistant” reply is:
    reply = response.choices[0].message["content"].strip()
    return reply
