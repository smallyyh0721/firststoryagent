"""
Issue Monitor - Continuously monitors RDMA and system health.
Detects anomalies and triggers the analysis pipeline.
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .rdma_collector import RDMACollector, RDMASnapshot
from .system_collector import SystemCollector, SystemSnapshot
from .switch_collector import SwitchCollector, SwitchSnapshot

logger = logging.getLogger(__name__)


@dataclass
class DetectedIssue:
    """Represents a detected RDMA/network issue."""
    issue_id: str = ""
    timestamp: str = ""
    severity: str = "warning"  # info, warning, critical
    category: str = ""  # link, performance, error_counter, fabric, system
    summary: str = ""
    details: dict = field(default_factory=dict)
    rdma_snapshot: dict = field(default_factory=dict)
    system_snapshot: dict = field(default_factory=dict)
    switch_snapshot: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "issue_id": self.issue_id,
            "timestamp": self.timestamp,
            "severity": self.severity,
            "category": self.category,
            "summary": self.summary,
            "details": self.details,
        }


class IssueMonitor:
    """
    Monitors RDMA infrastructure and detects issues automatically.
    Produces DetectedIssue objects for the Agent to analyze.
    """

    def __init__(self, poll_interval: int = 30, on_issue_detected=None):
        self.rdma = RDMACollector()
        self.system = SystemCollector()
        self.switch = SwitchCollector()
        self.poll_interval = poll_interval
        self.on_issue_detected = on_issue_detected  # async callback
        self._running = False
        self._issue_counter = 0
        self._last_counters: dict = {}
        self._cooldown_map: dict = {}  # category -> last_alert_time

    async def start(self):
        """Start the monitoring loop."""
        self._running = True
        logger.info("IssueMonitor started (poll_interval=%ds)", self.poll_interval)
        while self._running:
            try:
                await self._poll_cycle()
            except Exception as e:
                logger.error("Monitor poll error: %s", e, exc_info=True)
            await asyncio.sleep(self.poll_interval)

    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
        logger.info("IssueMonitor stopped")

    async def _poll_cycle(self):
        """Run one collection + detection cycle."""
        # Collect snapshots (run in executor to avoid blocking)
        loop = asyncio.get_event_loop()
        rdma_snap = await loop.run_in_executor(None, self.rdma.collect_all)
        sys_snap = await loop.run_in_executor(None, self.system.collect_all)
        switch_snap = await loop.run_in_executor(None, self.switch.collect_all)

        # Detect issues
        issues = self._detect_issues(rdma_snap, sys_snap, switch_snap)

        for issue in issues:
            logger.warning("Issue detected: [%s] %s", issue.severity, issue.summary)
            if self.on_issue_detected:
                await self.on_issue_detected(issue)

    def _next_issue_id(self) -> str:
        self._issue_counter += 1
        return f"RDMA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{self._issue_counter:04d}"

    def _detect_issues(
        self,
        rdma: RDMASnapshot,
        sys_snap: SystemSnapshot,
        switch: SwitchSnapshot,
    ) -> list[DetectedIssue]:
        """Run all detection rules and return list of issues."""
        issues = []
        now = datetime.utcnow()

        # Rule 1: RDMA error counters increasing
        if rdma.errors:
            # Check for new errors vs last snapshot
            new_errors = []
            for err in rdma.errors:
                counter_name = err["counter"]
                new_val = err["value"]
                old_val = self._last_counters.get(counter_name, 0)
                if new_val > old_val:
                    new_errors.append({**err, "delta": new_val - old_val})
            self._last_counters = {e["counter"]: e["value"] for e in rdma.errors}

            if new_errors:
                issues.append(DetectedIssue(
                    issue_id=self._next_issue_id(),
                    timestamp=now.isoformat(),
                    severity="critical" if any(e["delta"] > 100 for e in new_errors) else "warning",
                    category="error_counter",
                    summary=f"RDMA error counters increasing: {', '.join(e['counter'] for e in new_errors)}",
                    details={"new_errors": new_errors},
                    rdma_snapshot=rdma.raw_outputs,
                    system_snapshot=sys_snap.raw_outputs,
                ))

        # Rule 2: Link down detected
        for port_name, port_info in rdma.ports.items():
            state = port_info.get("state", "").lower()
            if "down" in state or "init" in state:
                issues.append(DetectedIssue(
                    issue_id=self._next_issue_id(),
                    timestamp=now.isoformat(),
                    severity="critical",
                    category="link",
                    summary=f"RDMA port {port_name} is {state}",
                    details={"port": port_name, "info": port_info},
                    rdma_snapshot=rdma.raw_outputs,
                ))

        # Rule 3: dmesg RDMA errors
        if rdma.dmesg_rdma:
            issues.append(DetectedIssue(
                issue_id=self._next_issue_id(),
                timestamp=now.isoformat(),
                severity="warning",
                category="system",
                summary=f"RDMA-related kernel errors detected ({len(rdma.dmesg_rdma)} entries)",
                details={"dmesg_lines": rdma.dmesg_rdma[:20]},
                rdma_snapshot=rdma.raw_outputs,
                system_snapshot=sys_snap.raw_outputs,
            ))

        # Rule 4: Switch/fabric errors
        if switch.switch_errors:
            issues.append(DetectedIssue(
                issue_id=self._next_issue_id(),
                timestamp=now.isoformat(),
                severity="warning",
                category="fabric",
                summary=f"Fabric link errors detected ({len(switch.switch_errors)} links)",
                details={"link_errors": switch.switch_errors[:20]},
                switch_snapshot=switch.raw_outputs,
            ))

        return issues

    async def run_manual_check(self) -> list[DetectedIssue]:
        """Run a single detection cycle manually (for API/UI)."""
        loop = asyncio.get_event_loop()
        rdma_snap = await loop.run_in_executor(None, self.rdma.collect_all)
        sys_snap = await loop.run_in_executor(None, self.system.collect_all)
        switch_snap = await loop.run_in_executor(None, self.switch.collect_all)
        return self._detect_issues(rdma_snap, sys_snap, switch_snap)
