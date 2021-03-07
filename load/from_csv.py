import csv

import typing

from load.phases import PhaseLoader, TurnRow
from load.setup import SetupLoader, SetupRow
from runner import Runner


def setup_from_csv(f: typing.TextIO) -> PhaseLoader:
    reader = csv.reader(f)
    loader = SetupLoader()
    current_header: typing.Optional[str] = None
    for row in reader:
        if not any(row):
            continue
        header = current_header if not row[0] else row[0]
        assert header
        loader.load_row(SetupRow(header, list(filter(None, row[1:6]))))

    return loader.create_phase_loader()


def turns_from_csv(f: typing.TextIO, through_row: typing.Optional[int] = None) -> typing.Iterable[TurnRow]:
    reader = csv.reader(f)
    is_header = True
    for idx, row in enumerate(reader, 1):
        if is_header:
            is_header = False
            continue
        if not any(row):
            continue
        if through_row is not None and idx > through_row:
            break
        yield TurnRow(*(cell.replace('[', '').replace(']', '') for cell in row[:5]))


def runner_from_csvs(
        setup_csv: typing.TextIO,
        turn_csv: typing.TextIO,
        through_row: typing.Optional[int] = None
) -> Runner:
    phase_loader = setup_from_csv(setup_csv)
    runner = Runner(phase_loader, turns_from_csv(turn_csv, through_row))
    return runner
