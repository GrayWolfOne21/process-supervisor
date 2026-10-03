import unittest
from pathlib import Path

from process_supervisor import Limits, Supervisor


class SupervisorTests(unittest.TestCase):
    def test_missing_binary_does_not_spawn(self):
        spawned = []
        sup = Supervisor(
            command=["/no/such/binary"],
            spawner=lambda cmd: spawned.append(cmd) or object(),
        )
        sup.step()
        sup.step()
        sup.step()
        self.assertEqual(spawned, [])
        self.assertIsNone(sup.process)
        self.assertEqual(sup.state.value, "MONITOR")

    def test_sensor_over_limit_stops_process(self):
        killed = []
        binary = Path(__file__)
        sup = Supervisor(
            command=[str(binary)],
            limits=Limits(max_temp_c=80, recovery_margin_c=8, log_every_s=10_000),
            sensor=lambda: 91.0,
            spawner=lambda cmd: "proc",
            killer=lambda proc: killed.append(proc),
        )
        for _ in range(4):
            sup.step()
        self.assertEqual(sup.state.value, "THERMAL_STOP")
        self.assertEqual(killed, ["proc"])
        self.assertIsNone(sup.process)

    def test_halt_stops_and_stays_halted(self):
        killed = []
        binary = Path(__file__)
        sup = Supervisor(
            command=[str(binary)],
            sensor=lambda: 40.0,
            spawner=lambda cmd: "proc",
            killer=lambda proc: killed.append(proc),
            limits=Limits(log_every_s=10_000),
        )
        for _ in range(4):
            sup.step()
        sup.halt()
        self.assertEqual(sup.state.value, "HALT")
        self.assertIsNone(sup.process)
        sup.step()
        self.assertEqual(sup.state.value, "HALT")
        sup.reengage()
        self.assertEqual(sup.state.value, "INIT")

    def test_missing_sensor_does_not_invent_a_stop(self):
        binary = Path(__file__)
        sup = Supervisor(
            command=[str(binary)],
            sensor=lambda: None,
            spawner=lambda cmd: "proc",
            limits=Limits(log_every_s=10_000),
        )
        for _ in range(5):
            sup.step()
        self.assertEqual(sup.state.value, "MONITOR")
        self.assertEqual(sup.process, "proc")


if __name__ == "__main__":
    unittest.main()
