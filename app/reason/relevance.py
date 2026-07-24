import re

from app.profile.load import relevance_terms

_TERMS = None


def _load():
    global _TERMS
    if _TERMS is None:
        _TERMS = [(t, re.compile(rf"\b{re.escape(t)}\b")) for t in relevance_terms()]
    return _TERMS


def is_relevant(opp):
    """Coarse gate: does any client-vocabulary term appear as a whole word?
    Deliberately high-recall - the reasoner makes the real call."""
    hay = f"{opp.get('title','')} {opp.get('description','') or ''}".lower()
    return any(rx.search(hay) for _, rx in _load())
