# process-supervisor

A process supervisor. It starts a command, watches a numeric sensor, and stops the process when the sensor crosses a limit or the operator halts it.

No protocol client. No network proxy. No template builder. If the binary is missing, it does not invent a running process.

```python
from process_supervisor import Supervisor, Limits

sup = Supervisor(
    command=["/usr/bin/sleep", "30"],
    limits=Limits(max_temp_c=85),
    sensor=lambda: 90.0,
)
```

## States

`INIT` → `EVALUATE` → `START` → `MONITOR`

From `MONITOR`:

- sensor over the limit → `THERMAL_STOP` (terminate, wait until it drops, return to `EVALUATE`)
- `halt()` → `HALT` until `reengage()`
- periodic → `LOG`, then back to `MONITOR`

## Run

```bash
python -m unittest discover -s tests
```

Python 3.10+. No third-party packages.

MIT. See [LICENSE](LICENSE).
