"""Pytest plugin simulating the step-2 flip: every grammar-less KB lazily gets the canonical grammar.

Marks on kb.registers (NOT id(kb)) — CPython reuses ids after GC, which made every earlier flip
number junk (plan §"EVERY EARLIER FLIP NUMBER WAS UNRELIABLE").
"""
import copy
import pathlib

import ugm.cnl.grammar_intake as gi
from ugm.cnl.grammar import load_grammar_file

LOUDON = pathlib.Path(r"C:\Users\ercas\creazioni\ugm\corpus\loudon_grammar.cnl")
_GRAM = load_grammar_file(LOUDON)          # parse the text ONCE (the 1.7s half)
_orig_session_banks = gi.session_banks
FLIP_MARK = "_flip_default_tried"


def _patched_session_banks(kb):
    b = _orig_session_banks(kb)
    if b is None and not kb.registers.get(FLIP_MARK):
        kb.registers[FLIP_MARK] = True
        try:
            gi.declare_grammar(kb, copy.deepcopy(_GRAM), open_class="noun")
        except Exception:
            return None
        b = _orig_session_banks(kb)
    return b


def pytest_configure(config):
    gi.session_banks = _patched_session_banks
