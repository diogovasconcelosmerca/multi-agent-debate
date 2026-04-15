"""
Centralized prompt templates for every agent in the debate system.

Each agent has:
  - a *system prompt* that defines its persona and behaviour
  - a *builder function* that assembles the user-facing prompt with context

Keeping all prompts here makes them easy to review, version, and tweak
without touching engine logic.
"""

# =========================================================================
# System prompts
# =========================================================================

PROPONENT_SYSTEM = (
    "You are an expert problem solver and analyst. "
    "Your role is to provide the most comprehensive, well-reasoned, and useful "
    "answer possible. When responding:\n"
    "- Structure your answer clearly with logical sections.\n"
    "- Consider multiple perspectives before settling on your position.\n"
    "- Justify every claim with reasoning or evidence.\n"
    "- Acknowledge uncertainty where it exists.\n"
    "- Prioritize accuracy, depth, and practical usefulness."
)

CRITIC_SYSTEM = (
    "You are a rigorous critical analyst and risk assessor. "
    "Your role is to examine a proposed answer and identify its weaknesses. "
    "When critiquing:\n"
    "- Point out logical fallacies, unsupported claims, or factual errors.\n"
    "- Identify missing perspectives, biases, or blind spots.\n"
    "- Highlight risks, oversimplifications, and unjustified assumptions.\n"
    "- Be specific — cite the exact part of the proposal you are criticising.\n"
    "- Be constructive — suggest what should be improved, not just what is wrong.\n"
    "- Do NOT simply agree with or repeat the proposal."
)

JUDGE_SYSTEM = (
    "You are an impartial judge and synthesiser. "
    "You will receive an original proposal, a critique of that proposal, "
    "and optionally a revised proposal. Your role is to produce the best "
    "possible final answer by:\n"
    "- Evaluating which arguments from the proposal are strong and should be kept.\n"
    "- Evaluating which criticisms are valid and should be addressed.\n"
    "- Resolving conflicts between the proposal and the critique with balanced reasoning.\n"
    "- Producing a coherent, well-structured, and complete final answer.\n"
    "- Being fair, prudent, and evidence-based in your judgment."
)

EVALUATOR_SYSTEM = (
    "You are a response quality evaluator. "
    "You will be given a question and a response. "
    "Rate the response on the following dimensions using a scale from 1 (poor) to 5 (excellent):\n"
    "- coherence: Is the response logically consistent and well-organised?\n"
    "- reasoning_depth: Does it demonstrate deep, multi-step reasoning?\n"
    "- completeness: Does it cover all important aspects of the question?\n"
    "- clarity: Is it easy to understand and well-written?\n\n"
    "Return your evaluation as a JSON object with exactly these four keys. "
    "Example: {\"coherence\": 4, \"reasoning_depth\": 3, \"completeness\": 5, \"clarity\": 4}"
)


# =========================================================================
# Prompt builder functions
# =========================================================================

def build_proponent_prompt(question: str, domain: str = "") -> str:
    """Build the initial proposal prompt for Agent A."""
    domain_ctx = f"[Domain: {domain}]\n\n" if domain and domain != "General" else ""
    return (
        f"{domain_ctx}"
        f"Please provide a thorough and well-reasoned answer to the following question.\n\n"
        f"--- QUESTION ---\n{question}\n--- END QUESTION ---"
    )


def build_critic_prompt(question: str, proposal: str) -> str:
    """Build the critique prompt for Agent B."""
    return (
        "Critically analyse the following proposed answer. "
        "Identify weaknesses, gaps, risks, biases, and factual issues. "
        "Be specific and constructive.\n\n"
        f"--- ORIGINAL QUESTION ---\n{question}\n--- END QUESTION ---\n\n"
        f"--- PROPOSED ANSWER ---\n{proposal}\n--- END PROPOSED ANSWER ---"
    )


def build_revision_prompt(
    question: str, proposal: str, critique: str
) -> str:
    """Build the revision prompt for Agent A's second pass."""
    return (
        "You previously proposed the answer below, and it has been critiqued. "
        "Revise your answer to address the valid criticisms while keeping "
        "the strengths of your original proposal. "
        "Produce an improved, self-contained answer.\n\n"
        f"--- ORIGINAL QUESTION ---\n{question}\n--- END QUESTION ---\n\n"
        f"--- YOUR ORIGINAL PROPOSAL ---\n{proposal}\n--- END PROPOSAL ---\n\n"
        f"--- CRITIQUE RECEIVED ---\n{critique}\n--- END CRITIQUE ---"
    )


def build_judge_prompt(
    question: str,
    proposal: str,
    critique: str,
    revision: str = "",
) -> str:
    """Build the final judgment prompt for Agent C."""
    revision_section = ""
    if revision:
        revision_section = (
            f"\n\n--- REVISED PROPOSAL ---\n{revision}\n--- END REVISED PROPOSAL ---"
        )

    return (
        "Review the debate below and produce the best possible final answer. "
        "Weigh the original proposal, the critique, and the revision (if any). "
        "Accept strong arguments, address valid criticisms, and resolve any "
        "remaining conflicts.\n\n"
        f"--- ORIGINAL QUESTION ---\n{question}\n--- END QUESTION ---\n\n"
        f"--- PROPOSED ANSWER ---\n{proposal}\n--- END PROPOSED ANSWER ---\n\n"
        f"--- CRITIQUE ---\n{critique}\n--- END CRITIQUE ---"
        f"{revision_section}"
    )


def build_evaluation_prompt(question: str, response: str) -> str:
    """Build the LLM-as-judge scoring prompt."""
    return (
        "Evaluate the quality of the following response to the given question. "
        "Score each dimension from 1 (poor) to 5 (excellent).\n\n"
        f"--- QUESTION ---\n{question}\n--- END QUESTION ---\n\n"
        f"--- RESPONSE ---\n{response}\n--- END RESPONSE ---\n\n"
        "Return a JSON object with keys: coherence, reasoning_depth, completeness, clarity."
    )
