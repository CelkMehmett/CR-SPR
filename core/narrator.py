"""DNA Narrator: generate human-friendly explanations for mutations.

Provides a template-based explainer and a small interface for plugging in an
LLM (OpenAI/HuggingFace) if available.
"""
from typing import Dict, Any, Optional
import textwrap


def template_explain(entry: Dict[str, Any]) -> str:
    gene = entry.get('gene')
    old = entry.get('old')
    new = entry.get('new')
    reward = entry.get('reward')
    success = entry.get('success')
    verb = 'improved' if success else 'reduced'
    s = f"Edited gene '{gene}' from {old:.4f} to {new:.4f}; this {verb} model reward to {reward:.4f}."
    return textwrap.fill(s, width=80)


class LLMHook:
    """Optional hook wrapper for external LLM calls. Implement `call(prompt)` to use."""
    def __init__(self, callable_obj=None):
        self.callable = callable_obj

    def is_available(self) -> bool:
        return callable(self.callable)

    def call(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError('LLM hook not configured')
        return self.callable(prompt)


def explain_with_llm(entry: Dict[str, Any], llm: Optional[LLMHook] = None) -> str:
    brief = template_explain(entry)
    if llm and llm.is_available():
        prompt = f"Summarize the following model mutation for a regulatory report:\n\n{brief}\n\nProvide a concise, non-technical one-sentence summary."
        try:
            resp = llm.call(prompt)
            return resp.strip()
        except Exception:
            return brief
    return brief
