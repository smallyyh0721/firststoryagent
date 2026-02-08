"""
Switch/fabric-level collector for Mellanox/NVIDIA switches.
Collects topology, port status, and error counters from the fabric.
"""

import subprocess
import logging
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SwitchSnapshot:
    """Snapshot of switch/fabric state."""
    timestamp: str = ""
    topology: dict = field(default_factory=dict)
    switch_errors: list = field(default_factory=list)
    raw_outputs: dict = field(default_factory=dict)


class SwitchCollector:
    """Collect switch and fabric information using ibdiagnet and related tools."""

    COMMANDS = {
        "iblinkinfo": "iblinkinfo 2>/dev/null || echo 'iblinkinfo not available'",
        "ibswitches": "ibswitches 2>/dev/null || echo 'ibswitches not available'",
        "ibnodes": "ibnodes 2>/dev/null || echo 'ibnodes not available'",
        "ibnetdiscover": "ibnetdiscover 2>/dev/null || echo 'ibnetdiscover not available'",
        "smpquery_portinfo": "smpquery portinfo 0 1 2>/dev/null || echo 'smpquery not available'",
        "ibdiagnet_summary": "cat /var/log/ibdiagnet2/ibdiagnet2.log 2>/dev/null | tail -200 || echo 'no ibdiagnet log'",
        "fabric_health": "ibdiagnet --get_phy_info 2>/dev/null || echo 'ibdiagnet not available'",
        "sm_status": "sminfo 2>/dev/null || echo 'sminfo not available'",
        "cable_info": "mlxcables 2>/dev/null || echo 'mlxcables not available'",
    }

    def _run_cmd(self, cmd: str, timeout: int = 60) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT] {cmd}"
        except Exception as e:
            return f"[ERROR] {e}"

    def collect_all(self) -> SwitchSnapshot:
        """Collect full switch/fabric snapshot."""
        snapshot = SwitchSnapshot(timestamp=datetime.utcnow().isoformat())

        for name, cmd in self.COMMANDS.items():
            snapshot.raw_outputs[name] = self._run_cmd(cmd)

        # Parse link errors from iblinkinfo
        snapshot.switch_errors = self._parse_link_errors(
            snapshot.raw_outputs.get("iblinkinfo", "")
        )

        return snapshot

    def _parse_link_errors(self, iblinkinfo_output: str) -> list:
        """Parse iblinkinfo output for error indicators."""
        errors = []
        for line in iblinkinfo_output.splitlines():
            lower = line.lower()
            # Detect down links, error states
            if any(kw in lower for kw in ["down", "error", "disabled", "polling"]):
                errors.append(line.strip())
        return errors

    def collect_fabric_topology(self) -> str:
        return self._run_cmd("ibnetdiscover 2>/dev/null || echo 'not available'")

    def collect_cable_health(self) -> str:
        return self._run_cmd("mlxcables 2>/dev/null || echo 'not available'")
