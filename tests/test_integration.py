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

    assert actual == expected


def test_red_wins_3p_trace() -> None:
    """Replay with trace mode and verify trace length and final state."""
    with open(EXAMPLE_DIR / "setup.csv") as setup, open(EXAMPLE_DIR / "moves.csv") as moves:
        runner = runner_from_csvs(setup, moves)
        trace = runner.run_with_trace()

    # 1 initial state + 57 turns
    assert len(trace) == 58
    assert trace[0]["mutable"]["completed"] is False
    assert trace[-1]["mutable"]["completed"] is True

    # Final trace entry should match expected output
    with open(EXAMPLE_DIR / "expected_output.json") as f:
        expected = json.load(f)

    assert trace[-1] == expected
