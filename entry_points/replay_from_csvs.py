#! /usr/bin/env python
import argparse
import json

import serialize
from load.from_csv import runner_from_csvs


def main(cmdline=None):
    arg_parser = argparse.ArgumentParser('Replay a game or part of a game from csv files')
    arg_parser.add_argument('--setup_csv', required=True)
    arg_parser.add_argument('--moves_csv', required=True)
    arg_parser.add_argument('--through_row', required=False, type=int,
                            help='Optional number of rows in moves_csv to play through')
    args = arg_parser.parse_args(cmdline)

    with open(args.setup_csv) as setup, open(args.moves_csv) as moves:
        runner = runner_from_csvs(setup, moves, through_row=args.through_row)
        runner.run()
        print(json.dumps(serialize.game_state(runner.game_state), indent=4))


if __name__ == '__main__':
    main()
