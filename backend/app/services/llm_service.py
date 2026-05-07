"""LLM service — OpenAI/compatible API integration for chemistry Q&A.

Used as fallback when rule-based KB doesn't have an answer.
"""
import logging
from typing import Optional, List, Dict

from app.config import OPENAI_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MoleculeAI Assistant, an expert computational chemist and drug discovery scientist.

Your role:
- Answer chemistry and drug discovery questions clearly and accurately
- Explain molecular properties, drug-likeness scores, and toxicity predictions
- Help users understand SMILES notation and molecular structures
- Provide guidance on drug development and optimization
- Be educational — explain concepts so non-experts can understand

Rules:
- Always be scientifically accurate
- Cite established rules (Lipinski, Veber, etc.) when relevant
- If uncertain, say so — don't make up data
- Keep responses focused and practical
- Use markdown formatting for readability
"""


async def llm_chat(
    user_message: str,
    history: List[Dict[str, str]] = None,
    molecule_context: Optional[dict] = None,
) -> tuple:
    """Send a question to the LLM and get a response.

    Returns:
        (reply_text, sources_list)
    """
    if not OPENAI_API_KEY:
        return (
            "LLM integration is not configured. Please set the `OPENAI_API_KEY` "
            "environment variable to enable AI-powered chat.\n\n"
            "In the meantime, try asking about specific topics like: "
            "LogP, SMILES, Lipinski rules, drug discovery, toxicity, solubility, "
            "blood-brain barrier, QED score, or Morgan fingerprints.",
            ["No API key configured"],
        )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add molecule context if available
        if molecule_context:
            context_str = "The user is currently analyzing a molecule with these properties:\n"
            for key, value in molecule_context.items():
                context_str += f"- {key}: {value}\n"
            messages.append({
                "role": "system",
                "content": f"Context about the user's molecule:\n{context_str}",
            })

        # Add conversation history
        if history:
            for msg in history[-10:]:  # Last 10 messages max
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1000,
        )

        reply = response.choices[0].message.content
        return reply, [f"OpenAI {LLM_MODEL}"]

    except ImportError:
        return (
            "The `openai` package is not installed. Run `pip install openai` to enable LLM chat.",
            ["Package not installed"],
        )
    except Exception as e:
        logger.error(f"LLM chat failed: {e}")
        return (
            f"I encountered an error connecting to the AI service. "
            f"Please try again later or ask about specific topics like LogP, SMILES, or drug discovery.",
            ["Error"],
        )
