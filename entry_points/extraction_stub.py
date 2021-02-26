#! /usr/bin/env python
import argparse
import json

import typing

import serialize
from analysis.extraction import extract_player_state_series
from load.from_csv import runner_from_csvs


def last(it: typing.Iterable):
    ran = False
    for foo in it:
        ran = True
    assert ran
    # noinspection PyUnboundLocalVariable
    return foo


def main(cmdline=None):
    arg_parser = argparse.ArgumentParser('Replay a game or part of a game from csv files')
    arg_parser.add_argument('--setup_csv', required=True)
    arg_parser.add_argument('--moves_csv', required=True)
    arg_parser.add_argument('--player', required=True)
    arg_parser.add_argument('--key', required=True)
    arg_parser.add_argument('--through_row', required=False,
                            help='Optional number of rows in moves_csv to play through')
    args = arg_parser.parse_args(cmdline)

    with open(args.setup_csv) as setup, open(args.moves_csv) as moves:
        runner = runner_from_csvs(setup, moves, through_row=args.through_row)
        state_series = runner.game_state_series()
        turn_ends = map(last, state_series)
        serialized = map(serialize.game_state, turn_ends)

        for update in extract_player_state_series(serialized, args.player, args.key):
            print(json.dumps(update))


if __name__ == '__main__':
    main()
