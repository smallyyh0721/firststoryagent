"""
Built-in diagnostic and remediation skills for RDMA troubleshooting.
New skills can be added here or registered dynamically at runtime.
"""

from .registry import Skill, SkillRegistry


def register_builtin_skills(registry: SkillRegistry):
    """Register all built-in RDMA diagnostic skills."""

    # ── RDMA Diagnostics ─────────────────────────────────────────────

    registry.register(Skill(
        name="check_rdma_counters",
        description="Read RDMA port error and performance counters using perfquery. "
                    "Use this to check for packet errors, link errors, and congestion.",
        category="diagnostics",
        command_template="perfquery -x {device} {port}",
        parameters=["device", "port"],
    ))

    registry.register(Skill(
        name="reset_rdma_counters",
        description="Reset RDMA port counters to zero. Use after confirming errors to see if they reoccur.",
        category="remediation",
        command_template="perfquery -R {device} {port}",
        parameters=["device", "port"],
        requires_sudo=True,
        risk_level="moderate",
    ))

    registry.register(Skill(
        name="check_port_state",
        description="Check the state and physical link info of an RDMA port using ibstat.",
        category="diagnostics",
        command_template="ibstat {device}",
        parameters=["device"],
    ))

    registry.register(Skill(
        name="check_rdma_link",
        description="Show RDMA link status for all devices or a specific device.",
        category="diagnostics",
        command_template="rdma link show",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_rdma_resources",
        description="Show RDMA resource usage including QPs, CQs, MRs, and PDs.",
        category="diagnostics",
        command_template="rdma res show",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_rdma_statistics",
        description="Show RDMA traffic statistics per device.",
        category="diagnostics",
        command_template="rdma statistic show",
        parameters=[],
    ))

    registry.register(Skill(
        name="run_ib_ping",
        description="Test RDMA connectivity to a remote node using ibping. "
                    "Requires ibping server running on the remote side.",
        category="diagnostics",
        command_template="ibping -c 5 {remote_lid}",
        parameters=["remote_lid"],
    ))

    registry.register(Skill(
        name="run_rdma_bandwidth_test",
        description="Run ib_write_bw to test RDMA write bandwidth to a remote node.",
        category="diagnostics",
        command_template="ib_write_bw -d {device} {remote_host} --duration 5",
        parameters=["device", "remote_host"],
    ))

    registry.register(Skill(
        name="run_rdma_latency_test",
        description="Run ib_write_lat to test RDMA write latency to a remote node.",
        category="diagnostics",
        command_template="ib_write_lat -d {device} {remote_host} -n 1000",
        parameters=["device", "remote_host"],
    ))

    # ── Network / Fabric Diagnostics ─────────────────────────────────

    registry.register(Skill(
        name="check_fabric_topology",
        description="Discover the InfiniBand fabric topology using ibnetdiscover.",
        category="diagnostics",
        command_template="ibnetdiscover",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_link_info",
        description="Show all link info in the fabric, including link speed, width, and errors.",
        category="diagnostics",
        command_template="iblinkinfo",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_sm_status",
        description="Check Subnet Manager (SM) status and identify active SM.",
        category="diagnostics",
        command_template="sminfo",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_cable_info",
        description="Check cable/transceiver health and type using mlxcables.",
        category="diagnostics",
        command_template="mlxcables",
        parameters=[],
    ))

    registry.register(Skill(
        name="run_ibdiagnet",
        description="Run ibdiagnet for comprehensive fabric health check. "
                    "This collects detailed diagnostic data from the entire fabric.",
        category="diagnostics",
        command_template="ibdiagnet --get_phy_info",
        parameters=[],
        requires_sudo=True,
        risk_level="moderate",
    ))

    # ── System Diagnostics ───────────────────────────────────────────

    registry.register(Skill(
        name="check_pci_link",
        description="Check PCIe link status for Mellanox/NVIDIA NICs. "
                    "Useful for detecting PCIe errors or speed downgrade.",
        category="diagnostics",
        command_template="lspci -vvv -s {pci_addr}",
        parameters=["pci_addr"],
    ))

    registry.register(Skill(
        name="check_irq_affinity",
        description="Check IRQ affinity settings for network devices. "
                    "Misaligned IRQ affinity can cause performance issues.",
        category="diagnostics",
        command_template="cat /proc/irq/{irq_num}/smp_affinity_list",
        parameters=["irq_num"],
    ))

    registry.register(Skill(
        name="check_mlx_firmware",
        description="Query Mellanox NIC firmware version using mlxfwmanager.",
        category="diagnostics",
        command_template="mlxfwmanager --query",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_ethtool_stats",
        description="Get detailed NIC statistics via ethtool for a given interface.",
        category="diagnostics",
        command_template="ethtool -S {interface}",
        parameters=["interface"],
    ))

    registry.register(Skill(
        name="check_dmesg",
        description="Check kernel message log for recent errors related to RDMA/Mellanox.",
        category="diagnostics",
        command_template="dmesg | grep -i -E 'mlx|ib_|rdma|infiniband|roce|error|fail' | tail -50",
        parameters=[],
    ))

    registry.register(Skill(
        name="check_ofed_version",
        description="Check installed OFED version and driver information.",
        category="diagnostics",
        command_template="ofed_info -s && modinfo mlx5_core | head -10",
        parameters=[],
    ))

    # ── RoCE Specific ────────────────────────────────────────────────

    registry.register(Skill(
        name="check_roce_config",
        description="Check RoCE (RDMA over Converged Ethernet) configuration "
                    "including ECN, PFC, and DSCP settings.",
        category="diagnostics",
        command_template="mlnx_qos -i {interface} && cma_roce_mode -d {device} -p {port}",
        parameters=["interface", "device", "port"],
    ))

    registry.register(Skill(
        name="check_pfc_counters",
        description="Check Priority Flow Control (PFC) counters on the interface.",
        category="diagnostics",
        command_template="ethtool -S {interface} | grep -i pfc",
        parameters=["interface"],
    ))

    registry.register(Skill(
        name="check_ecn_config",
        description="Check ECN (Explicit Congestion Notification) settings on the interface.",
        category="diagnostics",
        command_template="sysctl net.ipv4.tcp_ecn && mlnx_qos -i {interface}",
        parameters=["interface"],
    ))

    # ── Remediation ──────────────────────────────────────────────────

    registry.register(Skill(
        name="restart_rdma_port",
        description="Bounce (disable/enable) an RDMA port to attempt recovery. "
                    "WARNING: This will briefly disrupt traffic on this port.",
        category="remediation",
        command_template="ibportstate {device} {port} disable && sleep 2 && ibportstate {device} {port} enable",
        parameters=["device", "port"],
        requires_sudo=True,
        risk_level="dangerous",
    ))

    registry.register(Skill(
        name="reload_mlx_driver",
        description="Reload the mlx5 kernel driver. WARNING: This will disrupt all RDMA traffic.",
        category="remediation",
        command_template="modprobe -r mlx5_ib && modprobe -r mlx5_core && sleep 2 && modprobe mlx5_core && modprobe mlx5_ib",
        parameters=[],
        requires_sudo=True,
        risk_level="dangerous",
    ))

    registry.register(Skill(
        name="set_irq_affinity",
        description="Set optimal IRQ affinity for Mellanox interfaces using the built-in script.",
        category="remediation",
        command_template="/usr/sbin/set_irq_affinity.sh {interface}",
        parameters=["interface"],
        requires_sudo=True,
        risk_level="moderate",
    ))

    # ── General Utilities ────────────────────────────────────────────

    registry.register(Skill(
        name="run_command",
        description="Run an arbitrary shell command for advanced debugging. "
                    "Use only when no specific skill covers the need.",
        category="utility",
        command_template="{command}",
        parameters=["command"],
        risk_level="dangerous",
    ))

    registry.register(Skill(
        name="read_log_file",
        description="Read the last N lines of a log file.",
        category="utility",
        command_template="tail -n {lines} {filepath}",
        parameters=["filepath", "lines"],
    ))
