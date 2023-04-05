from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Generator, Optional


@dataclass
class Symbol:
    name: str
    type_: str
    kind: str
    index: int

    def __post_init__(self):
        types = ("int", "boolean", "char")
        if self.type_ not in types:
            if not self.type_.title()[0] == self.type_[0]:
                raise ValueError(f"Type is not one of {types} or a valid class name")
        if self.kind not in kinds:
            raise ValueError(f"Kind is not one of {kinds}")

    def __str__(self) -> str:
        return f"<{self.name},{self.type_},{self.kind},{self.index}>"


class SymbolTable:
    def __init__(
        self,
        class_name: str,
        table: Optional[dict[str, Symbol]] = None,
        counts: Optional[dict[str, int]] = None,
        label_generator: Optional[LabelGenerator] = None,
    ) -> None:
        self.class_name = class_name
        self.table = table or {}
        self.counts = counts or defaultdict(int)
        self.label_generator = label_generator or LabelGenerator()

    def add_symbol(self, name: str, type_: str, kind: str) -> SymbolTable:
        # print(
        #     f"Adding symbol {name} with kind {kind}, count for that kind:",
        #     self.counts[kind],
        # )
        self.table[name] = Symbol(
            name=name, type_=type_, kind=kind, index=self.counts[kind]
        )
        self.counts[kind] += 1
        return SymbolTable(self.class_name, self.table, self.counts)

    def __iter__(self) -> Generator:
        yield from list(self.table.keys())

    def __str__(self) -> str:
        rows = "\n".join([str(row) for row in self.table.values()])
        return f"{self.class_name}\n{rows}"


class LabelGenerator:
    def __init__(self, label_count: int = 0) -> None:
        self.label_count = label_count

    def generate_label(self) -> str:
        self.label_count += 1
        return f"L{self.label_count}"


class SubroutineTable(SymbolTable):
    def __init__(
        self,
        parent_table: SymbolTable,
        subroutine_name: str,
        is_method: bool = True,
        is_void: bool = False,
        is_constructor: bool = False,
        table: Optional[dict[str, Symbol]] = None,
        counts: Optional[dict[str, int]] = None,
    ) -> None:
        super().__init__(parent_table.class_name, table, counts)
        self.subroutine_name = subroutine_name
        self.is_method = is_method
        self.is_void = is_void
        self.is_constructor = is_constructor
        if not self.table and is_method:
            self.add_symbol(name="this", type_=parent_table.class_name, kind="argument")
        self.parent = parent_table

    @property
    def var_count(self) -> int:
        return [symbol.kind for symbol in self.table.values()].count("var")

    @property
    def field_count(self) -> int:
        print("field count")
        for key in self:
            print(self.get_symbol(key))
        field_count = [self.get_symbol(symbol).kind for symbol in self].count("field")
        print(f"{field_count=}")
        print("------")
        return field_count

    def get_symbol(self, key: str) -> Symbol:
        if key in self.table:
            return self.table[key]
        return self.parent.table[key]

    def __iter__(self) -> Generator:
        yield from list(self.table.keys()) + list(self.parent.table.keys())

    def __getitem__(self, key: str) -> str:
        symbol = self.table.get(key, None) or self.parent.table.get(key, None)
        if symbol is None:
            raise KeyError(key)
        memseg = symbol.kind
        if symbol.kind == "var":
            memseg = "local"
        elif symbol.kind == "field":
            memseg = "this"
        loc = f"{memseg} {symbol.index}"
        print(f"Accessing {symbol.name} @", loc)
        return loc

    def __str__(self) -> str:
        rows = "\n".join([str(row) for row in self.table.values()])
        return f"{self.class_name + '.' + self.subroutine_name}\n{rows}"


kinds = ("static", "field", "var", "argument")
