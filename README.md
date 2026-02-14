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

This will run `ruff` (linting and formatting), `mypy`, and `pytest` automatically on every commit. To run hooks manually:

```bash
pre-commit run --all-files
```

## Usage

### Replaying a Game from CSV Files

Replay a recorded game from setup and moves CSV files and print the final game state as JSON:

```bash
python -m istanbul_game.entry_points.replay_from_csvs \
    --setup_csv path/to/setup.csv \
    --moves_csv path/to/moves.csv
```

Use `--through_row N` to replay only the first N rows of moves.

### Extracting Player State Over Time

Track how a specific aspect of a player's state changes over the course of a game:

```bash
python -m istanbul_game.entry_points.extraction_stub \
    --setup_csv path/to/setup.csv \
    --moves_csv path/to/moves.csv \
    --player Red \
    --key inventory
```

This outputs one JSON object per turn showing snapshots, updates, and removed keys for the specified player and state key.

### Running the Example Game

Run a hardcoded example game demonstrating the action API:

```bash
python -m istanbul_game.dev.example_game
```

## CSV Format

The entry points read game data from two CSV files: a setup file describing the initial board state, and a moves file recording each turn.

### Setup CSV

The setup CSV has rows of the form `Header, value1, value2, ...` (up to 5 values). Empty rows are skipped. Recognized headers (case-insensitive, spaces become underscores):

| Header | Values | Description |
|---|---|---|
| `Names` | (ignored) | Optional player names, not used by the engine |
| `Order` | Player colors | Turn order, e.g. `Blue, Yellow, Red, Green` |
| `Governor` | Location number | Starting location of the governor |
| `Smuggler` | Location number | Starting location of the smuggler |
| `Small market` | Demand string | Initial small market demand, e.g. `2RG2Y` (2 red, 1 green, 2 yellow) |
| `Large market` | Demand string | Initial large market demand |
| `Cards` | Card names | Starting card for each player (same count as Order), e.g. `1Good, SellAny, ReturnAssistant, ArrestFamily` |
| `Location spec` | `Roll` or `Direct` | Whether location numbers refer to roll-based positions or direct board positions |
| `Tile locations` | 4 tile names | Board layout in groups of 4 (4 rows = 16 tiles). Tile names are prefix-matched, e.g. `Fruit` matches `Fruit Warehouse` |

**Demand strings** encode goods compactly: `R` = red/fabric, `G` = green/spice, `Y` = yellow/fruit, `B` = blue/jewelry. A preceding number indicates quantity, e.g. `2RG2Y` means 2 red + 1 green + 2 yellow.

**Card names** use camelCase and support several aliases: `1Good`/`OneGood`, `5Lira`/`FiveLira`, `ExtraMove`/`Move34`, `NoMove`/`Move0`/`StayPut`, `ReturnAssistant`, `ArrestFamily`, `SellAny`/`SmallMarket`, `2xSultan`/`DoubleSultan`, `2xPostOffice`/`DoublePostOffice`, `2xGemstoneDealer`/`DoubleGemstoneDealer`.

### Moves CSV

The moves CSV has a header row followed by one row per turn. Each row has 5 columns:

| Column | Phase | Description |
|---|---|---|
| Move | 1-2 | Movement and phase 1 actions |
| Action | 3 | Tile action |
| Rewards | 4 | Reward choices (from bonus cards, family member, etc.) |
| Gov | 4 | Governor encounter |
| Smug | 4 | Smuggler encounter |

Within each column, multiple actions are separated by `;`. Empty columns mean no action for that phase.

#### Move column

- **Location number**: Move to that location, e.g. `5`
- **`!` suffix on location**: Skip assistant placement (triggers early yield), e.g. `5!`
- **`!$` suffix on column**: Skip payment to other players at destination
- **`Card` prefix**: Play a card, e.g. `Card-ExtraMove 7` (extra move to location 7), `Card-NoMove`, `Card-ReturnAssistant 3` (return assistant from location 3)
- **`YellowTile N`**: Use yellow tile to return assistant from location N

#### Action column

- **(empty)**: Take the generic tile action (warehouses, post office, wainwright, gemstone dealer, fountain with all assistants)
- **`!`**: Skip the tile action
- **Good codes**: For mosques (`R`, `G`, etc.), sultan's palace (`RGY`), markets (`RG 2BY` = sell red+green, new demand is 2 blue + yellow)
- **`All`**: Sell all matching goods at a market; return all assistants at fountain
- **`Card` prefix**: Play a phase 3 card, e.g. `Card-DoubleSultan RG RBY`
- **Black market**: `G 3+4` (choose green, roll 3+4)
- **Tea house**: `5 2+4` (call 5, roll 2+4)
- **Caravansary**: `1Good Discard 5Lira` (gain OneGood card + top of discard, pay FiveLira card)
- **Police station**: `N <action>` (location number, then the action for the destination tile)
- **Fountain with specific assistants**: `3 7 12` (return assistants from locations 3, 7, 12)
- **`GreenTile G`**: Use green tile at a warehouse for an extra good
- **`RedTile 2+3 F 4+3`**: Use red tile to modify a die roll (initial roll, method `F`=set-to-four/`R`=reroll, final roll)

#### Rewards / Gov / Smug columns

- **Rewards**: `3`/`6`/`9`/`12` for lira (multiples of 3), or card names for card rewards
- **Governor**: `<gain> <cost> <roll>`, e.g. `1Good -2 3+4` (gain OneGood card, pay 2 lira, roll 3+4). Cost is `-2` for lira or a card name.
- **Smuggler**: `<gain> <cost> <roll>`, e.g. `B -2 1+5` (gain blue good, pay 2 lira, roll 1+5). Cost is `-2` for lira or a good code.
- Any column can also include `Card` actions (e.g. `Card-1Good R`) or `YellowTile N`.

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

### Linting and Formatting

Run the linter:
```bash
ruff check
```

Auto-fix lint issues:
```bash
ruff check --fix
```

Check formatting:
```bash
ruff format --check
```

Apply formatting:
```bash
ruff format
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

## License

See LICENSE file.
