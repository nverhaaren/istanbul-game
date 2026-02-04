import itertools
import typing

from ..lib.utils import extract_from_dict


def diff_dicts(d1, d2):
    if not isinstance(d1, dict) and not isinstance(d2, dict):
        return d2, set()
    removed_keys = set(d1) - set(d2)
    updates = {k: v for k, v in d2.items() if k not in d1}
    for k in set(d1) & set(d2):
        child_updates, child_removed = diff_dicts(d1[k], d2[k])
        if child_updates != {} and child_updates != d1[k]:
            updates[k] = child_updates
        removed_keys.update({f'{k}.{child_k}' for child_k in child_removed})
    return updates, removed_keys


def extract_player_state_series(states: typing.Iterator[dict], player: str, key: str):
    initial = next(states)
    player_count: int = initial['immutable']['player_count']
    idx_of_player = initial['immutable']['players'].index(player)
    previous = extract_from_dict(key, initial['mutable']['player_states'][idx_of_player])
    yield {'snapshot': previous, 'update': previous, 'removed_keys': [], 'when': ['initial']}

    before_source, after_source = itertools.tee(states, 2)
    before_states = (extract_from_dict(key, state['mutable']['player_states'][idx_of_player])
                     for idx, state in enumerate(before_source)
                     if (idx + 1) % player_count == idx_of_player)
    after_states = (extract_from_dict(key, state['mutable']['player_states'][idx_of_player])
                    for idx, state in enumerate(after_source)
                    if idx % player_count == idx_of_player)
    if idx_of_player == 0:
        before_states = itertools.chain([previous], before_states)

    for idx, (before, after) in enumerate(zip(before_states, after_states)):
        if previous != before:
            update_between, removed_between = diff_dicts(previous, before)
            yield {
                'snapshot': before,
                'update': update_between,
                'removed_keys': list(removed_between),
                'when': ['before', idx + 1],
            }
        if before != after:
            update_during, removed_during = diff_dicts(before, after)
            yield {
                'snapshot': after,
                'update': update_during,
                'removed_keys': list(removed_during),
                'when': ['after', idx + 1],
            }
        previous = after
