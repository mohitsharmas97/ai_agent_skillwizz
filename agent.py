import os
import json
import google.generativeai as genai
from tools import TOOLS, fetch_progress, suggest_next_topic
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ── Conversation memory ────────────────────────────────────────────────────────
conversation_history = []
current_user_id = None


# ── Tool executor ──────────────────────────────────────────────────────────────
def execute_tool(tool_name: str, user_id: str) -> str:
    """Run the requested tool and return result as string."""
    if tool_name not in TOOLS:
        return f"Unknown tool: {tool_name}"

    func = TOOLS[tool_name]["function"]
    result = func(user_id)
    return json.dumps(result, indent=2)


# ── Decide which tool to call based on user query ─────────────────────────────
def decide_tool(user_message: str) -> str | None:
    """Simple logic to decide which tool to invoke."""
    msg = user_message.lower()
    if any(word in msg for word in ["progress", "status", "how am i", "where am i", "my profile"]):
        return "fetch_progress"
    if any(word in msg for word in ["next", "today", "study", "suggest", "what should", "do next", "learn"]):
        return "suggest_next_topic"
    return None  # No tool needed, just chat


# ── Build system prompt ────────────────────────────────────────────────────────
def build_system_prompt() -> str:
    return """You are SkillWiz, a smart and encouraging AI learning assistant.
Your job is to help students stay on track with their learning journey.

You have access to two tools:
1. fetch_progress(user_id) → Gets student's full learning profile
2. suggest_next_topic(user_id) → Recommends what to study next

When tool results are provided to you, use that data to give a warm, 
personalized, and motivating response. 

Rules:
- Be friendly, concise, and encouraging
- Always use the student's name if available
- Mention their streak to motivate them
- Never give generic advice — always base it on their actual data
- If asked something unrelated to learning, politely redirect
"""


# ── Main agent function ────────────────────────────────────────────────────────
def chat(user_message: str, user_id: str) -> str:
    global conversation_history

    # Store user message in memory
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Decide if a tool should run
    tool_name = decide_tool(user_message)
    tool_result_text = ""

    if tool_name:
        tool_output = execute_tool(tool_name, user_id)
        tool_result_text = f"\n\n[TOOL: {tool_name} RESULT]\n{tool_output}\n"

    # Build full prompt with memory + tool result
    history_text = ""
    for msg in conversation_history[-6:]:  # last 3 turns for context
        role = "Student" if msg["role"] == "user" else "SkillWiz"
        history_text += f"{role}: {msg['content']}\n"

    full_prompt = f"""{build_system_prompt()}

Conversation so far:
{history_text}
{tool_result_text}
Now respond to the student's latest message as SkillWiz:"""

    # Call Gemini
    response = model.generate_content(full_prompt)
    reply = response.text.strip()

    # Store assistant reply in memory
    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return reply


# ── CLI Entry point ────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("       🎓 Welcome to SkillWiz AI Agent")
    print("=" * 55)

    # Get user ID
    user_id = input("\nEnter your User ID (e.g. user_123 or user_456): ").strip()
    if not user_id:
        user_id = "user_123"

    # Verify user exists
    result = fetch_progress(user_id)
    if "error" in result:
        print(f"\n❌ {result['error']}")
        return

    student_name = result["data"]["name"]
    print(f"\n✅ Hello {student_name}! I'm SkillWiz, your learning assistant.")
    print("   Ask me anything like:")
    print("   → 'What should I study today?'")
    print("   → 'Show my progress'")
    print("   → 'What's my next topic?'")
    print("\n   Type 'quit' to exit.\n")
    print("-" * 55)

    while True:
        user_input = input("\nYou: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ["quit", "exit", "bye"]:
            print("\nSkillWiz: Great work today! Keep the streak going! 🔥 Goodbye!\n")
            break

        print("\nSkillWiz: ", end="", flush=True)
        reply = chat(user_input, user_id)
        print(reply)
        print("-" * 55)


if __name__ == "__main__":
    main()
