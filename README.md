# Istanbul Game

A complete Python implementation of the Istanbul board game rules engine.

## Installation

Install the package in development mode with testing dependencies:

```bash
pip install -e ".[dev]"
```

### Pre-commit Hooks

Set up pre-commit hooks to run type checking and tests before each commit:

```bash
pre-commit install
```

This will run `mypy` and `pytest` automatically on every commit. To run hooks manually:

```bash
pre-commit run --all-files
```

## Development Commands

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

Run a specific test file:
```bash
pytest tests/test_game.py
```

### Type Checking

Run type checking with mypy:
```bash
mypy istanbul_game
```

### Coverage Reports

Generate a coverage report:
```bash
pytest --cov=istanbul_game --cov-report=term-missing
```

Generate an HTML coverage report:
```bash
pytest --cov=istanbul_game --cov-report=html
```

The HTML report will be available in `htmlcov/index.html`.

### Combined: Test + Coverage + Type Check

Run all quality checks:
```bash
pytest --cov=istanbul_game --cov-report=term-missing && mypy istanbul_game
```

## Project Structure

```
istanbul_game/
├── actions.py          # Player action definitions
├── constants.py        # Game constants (locations, cards, goods, etc.)
├── game.py            # Main GameState class with game mechanics
├── player.py          # Player state
├── tiles.py           # Tile state implementations
├── turn.py            # Turn state management
├── runner.py          # Game runner
├── serialize.py       # Game state serialization
├── load/              # Loading game states from various formats
├── analysis/          # Game analysis utilities
├── entry_points/      # Executable entry points
├── dev/               # Development examples
└── lib/               # Utility classes
```

## Architecture

### Game State Management

The `GameState` class (game.py:24) is the central orchestrator, maintaining:
- Player states (location, inventory, lira, rubies, hand, family member)
- Tile states (players present, assistants, tile-specific state)
- Turn state (current player, phase)
- Board layout (location-to-tile mapping)

### Action System

All player actions inherit from `PlayerAction`. Actions are validated and applied through `GameState.take_action()`, which:
1. Validates the action is legal
2. Updates relevant state (player, tiles, turn)
3. Handles cascading effects (e.g., family member encounters)
4. Checks win conditions

### Phase Management

Turns have multiple phases:
1. Movement/Card play
2. Payment (if other players at location)
3. Tile action or encounter special NPCs (governor/smuggler)

## Running Example Game

```bash
python -m istanbul_game.dev.example_game
```

## License

See LICENSE file.
