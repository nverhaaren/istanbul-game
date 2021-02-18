from collections import MutableMapping
from typing import Optional, Mapping

import typing


KT = typing.TypeVar('KT')
VT = typing.TypeVar('VT')


class ImmutableMapping(Mapping[KT, VT]):
    def __init__(self, *args, **kwargs):
        self._mapping = dict(*args, **kwargs)

    def __getitem__(self, item: KT) -> VT:
        return self._mapping[item]

    def __len__(self):
        return len(self._mapping)

    def __iter__(self) -> typing.Iterator[KT]:
        return iter(self._mapping)


class _InvertibleMapping(Mapping[KT, VT]):
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
            self._inverted: _InvertibleMapping[VT, KT] = self.__class__((v, k) for k, v in self._mapping.items())
            self._inverted._bind(self)
        return self._inverted

    def __getitem__(self, item: KT) -> VT:
        return self._mapping[item]

    def __len__(self):
        return len(self._mapping)

    def __iter__(self) -> typing.Iterator[KT]:
        return iter(self._mapping)


class ImmutableInvertibleMapping(_InvertibleMapping[KT, VT]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hash = None

    @property
    def inverse(self):
        return typing.cast(ImmutableInvertibleMapping[VT, KT], super().inverse)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(tuple(self.items()))
        return self._hash


class InvertibleMapping(_InvertibleMapping, MutableMapping):
    @property
    def inverse(self):
        return typing.cast(InvertibleMapping[VT, KT], super().inverse)

    def __setitem__(self, key: KT, value: VT):
        inverse = self.inverse
        if value in inverse:
            raise KeyError('{} is already bound to {}, setting again would destroy invertibility'.format(
                value, inverse[value]))
        self._mapping[key] = value
        inverse._mapping[value] = key

    def __delitem__(self, key: KT):
        value = self._mapping[key]
        del self._mapping[key]
        if self._inverted is not None:
            del self._inverted._mapping[value]
