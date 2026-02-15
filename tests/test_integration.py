"""Integration test: replay a complete game from CSV and verify the final state."""

import json
from pathlib import Path

from istanbul_game import serialize
from istanbul_game.constants import Player
from istanbul_game.load.from_csv import runner_from_csvs

EXAMPLE_DIR = Path(__file__).resolve().parent.parent / "examples" / "red_wins_3p"


def test_red_wins_3p_from_csv() -> None:
    """Replay the red_wins_3p example game and verify the final state matches expected output."""
    with open(EXAMPLE_DIR / "setup.csv") as setup, open(EXAMPLE_DIR / "moves.csv") as moves:
        runner = runner_from_csvs(setup, moves)
        runner.run()

    gs = runner.game_state
    assert gs.completed
    assert gs.player_states[Player.RED].rubies == 5

    actual = serialize.game_state(gs)
    with open(EXAMPLE_DIR / "expected_output.json") as f:
        expected = json.load(f)

    # Compare with normalization to handle set ordering differences in serialized lists
    assert _normalize(actual) == _normalize(expected)


def _normalize(obj: object) -> object:
    """Normalize JSON-like objects for comparison, sorting list elements where possible."""
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        normalized = [_normalize(x) for x in obj]
        if all(isinstance(x, (str, int, float, bool)) for x in normalized):
            return sorted(normalized, key=str)
        return normalized
    return obj
