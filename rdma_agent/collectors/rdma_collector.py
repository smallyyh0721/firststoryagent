"""
RDMA log and statistics collector.
Collects data from Mellanox/NVIDIA OFED stack, ibverbs, perfquery, etc.
"""

import subprocess
import logging
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RDMASnapshot:
    """Point-in-time snapshot of RDMA state."""
    timestamp: str = ""
    devices: list = field(default_factory=list)
    ports: dict = field(default_factory=dict)
    counters: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    dmesg_rdma: list = field(default_factory=list)
    raw_outputs: dict = field(default_factory=dict)


class RDMACollector:
    """Collect RDMA device info, counters, errors, and logs."""

    # Commands to collect RDMA information
    COMMANDS = {
        "ibstat": "ibstat",
        "ibstatus": "ibstatus",
        "ibdev2netdev": "ibdev2netdev",
        "rdma_devices": "rdma dev show",
        "rdma_link": "rdma link show",
        "rdma_res": "rdma res show",
        "rdma_stat": "rdma statistic show",
        "perfquery": "perfquery",
        "sminfo": "sminfo",
        "ibdiagnet_log": "cat /var/log/ibdiagnet2/ibdiagnet2.log 2>/dev/null || echo 'no ibdiagnet log'",
        "mlnx_fw": "mlxfwmanager --query 2>/dev/null || echo 'mlxfwmanager not available'",
        "ofed_info": "ofed_info -s 2>/dev/null || echo 'OFED not installed'",
        "dmesg_mlx": "dmesg | grep -i -E 'mlx|ib_|rdma|infiniband|roce' | tail -100",
        "syslog_rdma": "grep -i -E 'mlx|ib_|rdma|infiniband|roce' /var/log/syslog 2>/dev/null | tail -100 || echo 'no syslog entries'",
    }

    # Error patterns to detect in counter output
    ERROR_PATTERNS = [
        r"SymbolErrorCounter:\s*(\d+)",
        r"LinkErrorRecoveryCounter:\s*(\d+)",
        r"LinkDownedCounter:\s*(\d+)",
        r"PortRcvErrors:\s*(\d+)",
        r"PortRcvRemotePhysicalErrors:\s*(\d+)",
        r"PortRcvSwitchRelayErrors:\s*(\d+)",
        r"PortXmitDiscards:\s*(\d+)",
        r"PortXmitConstraintErrors:\s*(\d+)",
        r"PortRcvConstraintErrors:\s*(\d+)",
        r"LocalLinkIntegrityErrors:\s*(\d+)",
        r"ExcessiveBufferOverrunErrors:\s*(\d+)",
        r"VL15Dropped:\s*(\d+)",
        r"PortXmitWait:\s*(\d+)",
    ]

    def _run_cmd(self, cmd: str, timeout: int = 30) -> str:
        """Execute a shell command and return output."""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT] Command timed out: {cmd}"
        except Exception as e:
            return f"[ERROR] {e}"

    def collect_all(self) -> RDMASnapshot:
        """Collect a full RDMA snapshot."""
        snapshot = RDMASnapshot(timestamp=datetime.utcnow().isoformat())

        # Run all collection commands
        for name, cmd in self.COMMANDS.items():
            output = self._run_cmd(cmd)
            snapshot.raw_outputs[name] = output

        # Parse devices
        snapshot.devices = self._parse_devices(snapshot.raw_outputs.get("ibstat", ""))

        # Parse port info
        snapshot.ports = self._parse_ports(snapshot.raw_outputs.get("ibstatus", ""))

        # Parse error counters
        snapshot.counters, snapshot.errors = self._parse_counters(
            snapshot.raw_outputs.get("perfquery", "")
        )

        # Parse dmesg for RDMA errors
        snapshot.dmesg_rdma = self._parse_dmesg_errors(
            snapshot.raw_outputs.get("dmesg_mlx", "")
        )

        return snapshot

    def collect_port_counters(self, device: str = "", port: int = 1) -> dict:
        """Collect detailed port counters for a specific device/port."""
        cmd = f"perfquery -x {device} {port}" if device else "perfquery -x"
        output = self._run_cmd(cmd)
        counters, _ = self._parse_counters(output)
        return counters

    def collect_device_info(self) -> list[dict]:
        """Collect RDMA device information."""
        output = self._run_cmd("ibstat")
        return self._parse_devices(output)

    def _parse_devices(self, ibstat_output: str) -> list:
        """Parse ibstat output into device list."""
        devices = []
        current_device = None
        for line in ibstat_output.splitlines():
            line = line.strip()
            if line.startswith("CA '"):
                name = line.split("'")[1]
                current_device = {"name": name, "ports": []}
                devices.append(current_device)
            elif current_device and ":" in line:
                key, _, val = line.partition(":")
                current_device[key.strip().lower().replace(" ", "_")] = val.strip()
        return devices

    def _parse_ports(self, ibstatus_output: str) -> dict:
        """Parse ibstatus output into port dict."""
        ports = {}
        current_port = None
        for line in ibstatus_output.splitlines():
            line = line.strip()
            if line.startswith("Infiniband device"):
                parts = line.split("'")
                if len(parts) >= 2:
                    port_name = parts[1]
                    current_port = {"name": port_name}
                    ports[port_name] = current_port
            elif current_port and ":" in line:
                key, _, val = line.partition(":")
                current_port[key.strip().lower().replace(" ", "_")] = val.strip()
        return ports

    def _parse_counters(self, perfquery_output: str) -> tuple[dict, list]:
        """Parse perfquery output, return (counters_dict, error_list)."""
        counters = {}
        errors = []
        for pattern in self.ERROR_PATTERNS:
            match = re.search(pattern, perfquery_output)
            if match:
                name = pattern.split(r":\s*")[0].replace("\\", "")
                value = int(match.group(1))
                counters[name] = value
                if value > 0 and name not in ("PortXmitWait",):
                    errors.append({"counter": name, "value": value})
        return counters, errors

    def _parse_dmesg_errors(self, dmesg_output: str) -> list:
        """Extract RDMA-related error lines from dmesg."""
        error_keywords = ["error", "fail", "timeout", "reset", "down", "drop", "lost"]
        errors = []
        for line in dmesg_output.splitlines():
            lower = line.lower()
            if any(kw in lower for kw in error_keywords):
                errors.append(line.strip())
        return errors
