from collections import MutableMapping
from typing import Optional, Mapping


class ImmutableMapping(Mapping):
    def __init__(self, *args, **kwargs):
        self._mapping = dict(*args, **kwargs)

    def __getitem__(self, item):
        return self._mapping[item]

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)


class _InvertibleMapping(Mapping):
    def __init__(self, *args, **kwargs):
        self._mapping = dict(*args, **kwargs)
        if len(set(self._mapping.values())) != len(self._mapping):
            raise TypeError('Mapping is not injective/invertible')
        self._inverted: Optional[_InvertibleMapping] = None

    def _bind(self, inverse):
        self._inverted: _InvertibleMapping = inverse

    @property
    def inverse(self):
        if self._inverted is None:
            self._inverted = self.__class__((v, k) for k, v in self._mapping.items())
            self._inverted._bind(self)
        return self._inverted

    def __getitem__(self, item):
        return self._mapping[item]

    def __len__(self):
        return len(self._mapping)

    def __iter__(self):
        return iter(self._mapping)


class ImmutableInvertibleMapping(_InvertibleMapping):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hash = None

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(self.items()))
        return self._hash


class InvertibleMapping(_InvertibleMapping, MutableMapping):
    def __setitem__(self, key, value):
        inverse = self.inverse
        if value in inverse:
            raise KeyError('{} is already bound to {}, setting again would destroy invertibility'.format(
                value, inverse[value]))
        self._mapping[key] = value
        inverse._mapping[value] = key

    def __delitem__(self, key):
        value = self._mapping[key]
        del self._mapping[key]
        if self._inverted is not None:
            del self._inverted._mapping[value]
