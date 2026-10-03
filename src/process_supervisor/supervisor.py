"""Fail-closed process loop. A missing binary is not a running process."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Sequence


class State(str, Enum):
    INIT = "INIT"
    EVALUATE = "EVALUATE"
    START = "START"
    MONITOR = "MONITOR"
    THERMAL_STOP = "THERMAL_STOP"
    HALT = "HALT"
    LOG = "LOG"


HALT = State.HALT


@dataclass(frozen=True)
class Limits:
    max_temp_c: float = 85.0
    recovery_margin_c: float = 8.0
    log_every_s: float = 30.0


@dataclass
class Supervisor:
    command: Sequence[str]
    limits: Limits = field(default_factory=Limits)
    sensor: Callable[[], float | None] = lambda: None
    clock: Callable[[], float] = time.time
    spawner: Callable[[Sequence[str]], object | None] | None = None
    killer: Callable[[object], None] | None = None

    def __post_init__(self) -> None:
        self.state = State.INIT
        self.halted = False
        self.process: object | None = None
        self.temp_c: float | None = None
        self.logs: list[str] = []
        self._last_log = 0.0
        if self.spawner is None:
            self.spawner = self._default_spawn
        if self.killer is None:
            self.killer = self._default_kill

    def step(self) -> State:
        if self.halted and self.state is not State.HALT:
            self._stop()
            self.state = State.HALT
            return self.state
        if self.state is State.INIT:
            self.state = State.EVALUATE
        elif self.state is State.EVALUATE:
            self.state = State.START
        elif self.state is State.START:
            self._start()
        elif self.state is State.MONITOR:
            self._monitor()
        elif self.state is State.THERMAL_STOP:
            self._cool()
        elif self.state is State.LOG:
            self.logs.append(f"{self.clock():.0f} {self.temp_c}")
            self._last_log = self.clock()
            self.state = State.MONITOR
        return self.state

    def halt(self) -> None:
        self.halted = True
        self._stop()
        self.state = State.HALT

    def reengage(self) -> None:
        self.halted = False
        self.state = State.INIT

    def _start(self) -> None:
        if self.process is not None:
            self.state = State.MONITOR
            return
        binary = Path(self.command[0])
        if not binary.exists():
            self.process = None
            self.state = State.MONITOR
            return
        self.process = self.spawner(self.command) if self.spawner else None
        self.state = State.MONITOR

    def _monitor(self) -> None:
        self.temp_c = self.sensor()
        if self.temp_c is not None and self.temp_c > self.limits.max_temp_c:
            self._stop()
            self.state = State.THERMAL_STOP
            return
        if self.clock() - self._last_log >= self.limits.log_every_s:
            self.state = State.LOG
            return
        self.state = State.MONITOR

    def _cool(self) -> None:
        self.temp_c = self.sensor()
        recovery = self.limits.max_temp_c - self.limits.recovery_margin_c
        if self.temp_c is None or self.temp_c <= recovery:
            self.state = State.EVALUATE
            return
        self.state = State.THERMAL_STOP

    def _stop(self) -> None:
        if self.process is not None and self.killer:
            self.killer(self.process)
        self.process = None

    @staticmethod
    def _default_spawn(command: Sequence[str]) -> object | None:
        return None

    @staticmethod
    def _default_kill(process: object) -> None:
        return None
