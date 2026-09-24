"""Pure domain logic: no I/O, no clock, no database.

Everything here is a plain function or dataclass so it can be unit-tested directly and
reused by the simulator's analysis tools (architecture.md §2).
"""
