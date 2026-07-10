"""CNL (Controlled Natural Language) layer for the Universal Graph Machine."""
from .forms import tokenize, load_text, FORM_RULES
from .authoring import load_facts, load_rules, run_rules, expand_rules
from .surface import explain, narrate
from .query import ask, ask_goal, recognize
from .machine_rules import load_machine_rules
from .universal import UNIVERSAL_RULES
