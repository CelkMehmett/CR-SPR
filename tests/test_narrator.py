import os
import sys

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from core.narrator import template_explain, explain_with_llm, LLMHook


def test_template_explain():
    entry = {'gene': 'g1', 'old': 0.1, 'new': 0.2, 'reward': 0.5, 'success': True}
    s = template_explain(entry)
    assert 'Edited gene' in s


def test_explain_with_fake_llm():
    entry = {'gene': 'g2', 'old': -0.1, 'new': 0.0, 'reward': 0.1, 'success': False}
    # fake llm
    llm = LLMHook(callable_obj=lambda p: 'LLM SUMMARY: This change reduced risk and boosted stability.')
    out = explain_with_llm(entry, llm=llm)
    assert out.startswith('LLM SUMMARY')
