import typing
from collections.abc import Iterator, Mapping, MutableMapping, MutableSet
from typing import Optional

KT = typing.TypeVar("KT")
VT = typing.TypeVar("VT")
T = typing.TypeVar("T")


class OrderedSet(MutableSet[T]):
    """A set that preserves insertion order, backed by a dict."""

    def __init__(self, iterable: typing.Iterable[T] = ()) -> None:
        self._data: dict[T, None] = dict.fromkeys(iterable)

    def __contains__(self, x: object) -> bool:
        return x in self._data

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def add(self, value: T) -> None:
        self._data[value] = None

    def discard(self, value: T) -> None:
        self._data.pop(value, None)

    def __repr__(self) -> str:
        if not self._data:
            return f"{type(self).__name__}()"
        return f"{type(self).__name__}({list(self._data)})"

    def __ior__(self, other: typing.AbstractSet[T]) -> "OrderedSet[T]":  # type: ignore[override, misc]
        for item in other:
            self._data[item] = None
        return self

    def __isub__(self, other: typing.AbstractSet[T]) -> "OrderedSet[T]":
        for item in other:
            self._data.pop(item, None)
        return self

    def __sub__(self, other: typing.AbstractSet[T]) -> "OrderedSet[T]":
        return OrderedSet(item for item in self if item not in other)


class ImmutableMapping(Mapping[KT, VT]):
    _mapping: dict[KT, VT]

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._mapping = dict(*args, **kwargs)

    def __getitem__(self, item: KT) -> VT:
        return self._mapping[item]

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self) -> typing.Iterator[KT]:
        return iter(self._mapping)


class _InvertibleMapping(Mapping[KT, VT]):
    _mapping: dict[KT, VT]
    _inverted: Optional["_InvertibleMapping[VT, KT]"]

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._mapping = dict(*args, **kwargs)
        if len(set(self._mapping.values())) != len(self._mapping):
            raise TypeError("Mapping is not injective/invertible")
        self._inverted = None

    def _bind(self, inverse: "_InvertibleMapping[VT, KT]") -> None:
        self._inverted = inverse

    @property
    def inverse(self) -> "_InvertibleMapping[VT, KT]":
        if self._inverted is None:
            # Cast needed because self.__class__ returns same type params, but swapping k,v inverts them
            inverted = typing.cast(
                "_InvertibleMapping[VT, KT]", self.__class__((v, k) for k, v in self._mapping.items())
            )
            inverted._bind(self)
            self._inverted = inverted
        return self._inverted

    def __getitem__(self, item: KT) -> VT:
        return self._mapping[item]

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self) -> typing.Iterator[KT]:
        return iter(self._mapping)


class ImmutableInvertibleMapping(_InvertibleMapping[KT, VT]):
    _hash: int | None

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self._hash = None

    @property
    def inverse(self) -> "ImmutableInvertibleMapping[VT, KT]":
        return typing.cast("ImmutableInvertibleMapping[VT, KT]", super().inverse)

    def __hash__(self) -> int:
        if self._hash is None:
            self._hash = hash(tuple(self.items()))
        return self._hash


class InvertibleMapping(_InvertibleMapping[KT, VT], MutableMapping[KT, VT]):
    @property
    def inverse(self) -> "InvertibleMapping[VT, KT]":
        return typing.cast("InvertibleMapping[VT, KT]", super().inverse)

    def __setitem__(self, key: KT, value: VT) -> None:
        inverse = self.inverse
        if value in inverse:
            raise KeyError(f"{value} is already bound to {inverse[value]}, setting again would destroy invertibility")
        self._mapping[key] = value
        inverse._mapping[value] = key

    def __delitem__(self, key: KT) -> None:
        value = self._mapping[key]
        del self._mapping[key]
        if self._inverted is not None:
            del self._inverted._mapping[value]


def extract_from_dict(key: str, d: dict) -> typing.Any:
    assert key
    if key[0] == ".":
        key = key[1:]
    keys = key.split(".")
    result = d
    for k in keys:
        result = result[k]
    return result
