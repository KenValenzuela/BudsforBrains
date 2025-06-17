# chat_guard.py — LangChain-enhanced Restriction Layer for Cannabis Assistant
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

# === Initialize LLM ===
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.0)

# === Prompt Template for Classification ===
prompt = PromptTemplate.from_template(
    """
    You are a strict domain classifier for a cannabis assistant.
    Only answer 'YES' or 'NO'.

    If the question below is about cannabis, strains, terpenes, cannabinoids, weed effects,
    usage advice, or related topics like indica/sativa or THC/CBD:
    → reply YES

    Otherwise (weather, general advice, jokes, food, politics, etc.):
    → reply NO

    Question: {input}
    """
)

chain = LLMChain(llm=llm, prompt=prompt)


def should_answer(text: str) -> bool:
    try:
        result = chain.run(text).strip().upper()
        return result.startswith("YES")
    except Exception as e:
        print("⚠️ Domain check failed, falling back to keywords:", e)
        fallback_keywords = ["cannabis", "weed", "strain", "terpene", "thc", "cbd", "indica", "sativa", "hybrid", "entourage"]
        return any(kw in text.lower() for kw in fallback_keywords)


def explain_restriction():
    return (
        "🚫 This assistant only answers cannabis-related questions.\n"
        "Try asking things like:\n"
        "- What is the difference between indica and sativa?\n"
        "- What strain helps with focus?\n"
        "- How does myrcene affect the high?"
    )
