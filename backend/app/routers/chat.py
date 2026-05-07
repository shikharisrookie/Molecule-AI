"""Chat router — /chat endpoint.

Combines rule-based chemistry KB with optional LLM fallback.
"""
from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chemistry_kb import answer_chemistry_question
from app.services.llm_service import llm_chat
from app.services.chemistry import parse_smiles, get_molecular_properties

router = APIRouter(prefix="/chat", tags=["AI Chemistry Assistant"])


@router.post("", response_model=ChatResponse, summary="Ask a chemistry question")
async def chat(request: ChatRequest):
    """
    AI-powered chemistry assistant.

    - First tries the rule-based knowledge base (instant, free, offline)
    - Falls back to LLM (OpenAI) for open-ended questions
    - Optionally accepts a SMILES string for molecule-aware responses
    """
    # Build molecule context if SMILES provided
    mol_context = None
    if request.context_smiles:
        mol = parse_smiles(request.context_smiles)
        if mol:
            mol_context = get_molecular_properties(mol)

    # Try rule-based KB first
    kb_answer, kb_sources = answer_chemistry_question(
        request.message, molecule_context=mol_context,
    )

    if kb_answer:
        return ChatResponse(
            success=True,
            reply=kb_answer,
            sources=kb_sources,
        )

    # Fall back to LLM
    try:
        history_dicts = [
            {"role": msg.role, "content": msg.content}
            for msg in request.history
        ]
        llm_reply, llm_sources = await llm_chat(
            user_message=request.message,
            history=history_dicts,
            molecule_context=mol_context,
        )
        return ChatResponse(
            success=True,
            reply=llm_reply,
            sources=llm_sources,
        )
    except Exception as e:
        return ChatResponse(
            success=False,
            reply="I couldn't process your question. Please try rephrasing it or ask about a specific chemistry topic.",
            error=str(e),
        )
