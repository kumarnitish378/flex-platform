"""Closed-loop SimPy simulator for the Smart Cab platform.

Black-box by construction: agents drive the platform through its public REST, WebSocket
and MQTT interfaces and never import backend internals (`coding-standards.md` §4).
"""

__version__ = "0.1.0"
