"""
System-level collector for CPU, memory, network, and OS logs.
"""

import subprocess
import logging
import platform
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SystemSnapshot:
    """Point-in-time snapshot of system state."""
    timestamp: str = ""
    cpu_info: dict = field(default_factory=dict)
    memory_info: dict = field(default_factory=dict)
    network_stats: dict = field(default_factory=dict)
    kernel_info: dict = field(default_factory=dict)
    pci_devices: list = field(default_factory=list)
    raw_outputs: dict = field(default_factory=dict)


class SystemCollector:
    """Collect system-level information relevant to RDMA diagnosis."""

    COMMANDS = {
        "cpu_usage": "mpstat 1 1 2>/dev/null || top -bn1 | head -20",
        "memory": "free -h",
        "interrupts": "cat /proc/interrupts | head -50",
        "softirqs": "cat /proc/softirqs",
        "netstat": "ss -s",
        "ip_link": "ip link show",
        "ip_addr": "ip addr show",
        "ethtool_all": "for dev in $(ip -o link show | awk -F': ' '{print $2}'); do echo \"=== $dev ===\"; ethtool $dev 2>/dev/null; ethtool -S $dev 2>/dev/null | head -30; done",
        "pci_mlx": "lspci | grep -i -E 'mellanox|nvidia|infiniband|ethernet'",
        "kernel_version": "uname -a",
        "modules_rdma": "lsmod | grep -i -E 'mlx|ib_|rdma|roce'",
        "irq_affinity": "cat /proc/irq/*/smp_affinity_list 2>/dev/null | head -50 || echo 'no irq info'",
        "numa_info": "numactl --hardware 2>/dev/null || echo 'numactl not available'",
        "sysctl_net": "sysctl net.core net.ipv4.tcp_ecn net.ipv4.tcp_timestamps 2>/dev/null | head -30",
        "dmesg_errors": "dmesg --level=err,warn | tail -50",
    }

    def _run_cmd(self, cmd: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return f"[TIMEOUT] {cmd}"
        except Exception as e:
            return f"[ERROR] {e}"

    def collect_all(self) -> SystemSnapshot:
        """Collect full system snapshot."""
        snapshot = SystemSnapshot(timestamp=datetime.utcnow().isoformat())

        for name, cmd in self.COMMANDS.items():
            snapshot.raw_outputs[name] = self._run_cmd(cmd)

        snapshot.kernel_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        }

        return snapshot

    def collect_cpu_stats(self) -> str:
        return self._run_cmd("mpstat 1 1 2>/dev/null || top -bn1 | head -20")

    def collect_network_stats(self) -> str:
        return self._run_cmd("ip -s link show")

    def collect_pci_info(self) -> str:
        return self._run_cmd("lspci -vvv | grep -A 20 -i -E 'mellanox|nvidia'")
