from actions import MosqueAction
from load.core import load_good


def load_mosque_action(s: str) -> MosqueAction:
    good = load_good(s)
    return MosqueAction(good)
