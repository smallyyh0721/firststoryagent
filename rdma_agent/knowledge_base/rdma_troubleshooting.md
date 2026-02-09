# RDMA Troubleshooting Knowledge Base

## Link Down / Link Flapping

### Symptoms
- ibstat shows port state as "Down" or "Initializing"
- LinkDownedCounter increasing in perfquery output
- dmesg shows "mlx5_core: link down" messages
- Intermittent connectivity loss

### Common Root Causes
1. **Cable/transceiver failure**: Damaged fiber, dirty connectors, or failing transceivers
2. **Port configuration mismatch**: Speed/width mismatch between endpoints
3. **Subnet Manager issues**: SM not running or SM failover
4. **Firmware bug**: Known firmware issues with specific FW versions
5. **PCIe issues**: NIC not properly seated, PCIe link degradation

### Diagnostic Steps
1. Check port state: `ibstat`
2. Check error counters: `perfquery -x`
3. Check cable health: `mlxcables`
4. Check SM status: `sminfo`
5. Check firmware version: `mlxfwmanager --query`
6. Check dmesg for errors: `dmesg | grep -i mlx`
7. Check PCIe link: `lspci -vvv -s <pci_addr>`

### Resolution
- Clean or replace cable/transceiver
- Ensure matching port configuration on both ends
- Restart SM if needed
- Update firmware if known bug
- Reseat NIC if PCIe issue

---

## High Error Counters

### Symptoms
- PortRcvErrors, SymbolErrorCounter, or LinkErrorRecoveryCounter non-zero
- Performance degradation
- Packet retransmissions

### Common Root Causes
1. **Signal integrity**: Bad cable, dirty connector, excessive cable length
2. **EMI interference**: Running cables near power sources
3. **Speed mismatch**: Autonegotiation failure
4. **Switch port issue**: Faulty switch port

### Diagnostic Steps
1. Check all error counters: `perfquery -x`
2. Reset counters and re-check: `perfquery -R` then wait, then `perfquery -x`
3. Check cable info: `mlxcables`
4. Check link width/speed: `ibstat`
5. Try different cable
6. Try different switch port

---

## RoCE Performance Issues

### Symptoms
- Lower than expected bandwidth in ib_write_bw tests
- High latency in ib_write_lat tests
- ECN/PFC counter increases

### Common Root Causes
1. **PFC not configured**: Priority Flow Control needed for lossless RoCE
2. **ECN misconfiguration**: ECN thresholds too aggressive or disabled
3. **DSCP/ToS mismatch**: Traffic not in the correct priority class
4. **MTU mismatch**: Jumbo frames not enabled end-to-end
5. **IRQ affinity**: Interrupts not properly distributed across CPU cores
6. **NUMA misalignment**: Application and NIC on different NUMA nodes

### Diagnostic Steps
1. Check PFC config: `mlnx_qos -i <interface>`
2. Check ECN: `sysctl net.ipv4.tcp_ecn`
3. Check MTU: `ip link show`
4. Check IRQ affinity: `cat /proc/irq/*/smp_affinity_list`
5. Check NUMA: `numactl --hardware`
6. Run bandwidth test: `ib_write_bw -d <dev> <remote>`
7. Check PFC counters: `ethtool -S <iface> | grep pfc`

### Resolution
- Configure PFC: `mlnx_qos -i <iface> --pfc 0,0,0,1,0,0,0,0`
- Enable ECN: `sysctl -w net.ipv4.tcp_ecn=1`
- Set MTU: `ip link set <iface> mtu 9000`
- Fix IRQ affinity: `/usr/sbin/set_irq_affinity.sh <iface>`

---

## Subnet Manager Issues

### Symptoms
- Ports stuck in "Init" state
- sminfo shows no active SM
- Fabric routes not updating

### Diagnostic Steps
1. Check SM status: `sminfo`
2. Check SM logs: OpenSM log at /var/log/opensm.log
3. Check if opensm is running: `systemctl status opensm`
4. Check for multiple SMs: `saquery -s`

### Resolution
- Start SM: `systemctl start opensm`
- Check SM priority if multiple SMs configured
- Review opensm.conf for configuration issues

---

## PCIe Issues

### Symptoms
- NIC detected but not functioning properly
- Performance significantly below spec
- dmesg shows PCIe errors

### Diagnostic Steps
1. Check PCIe link status: `lspci -vvv -s <addr>`
2. Look for "LnkSta" line - should match "LnkCap"
3. Check for PCIe AER errors in dmesg
4. Check BIOS settings for PCIe slot configuration

### Resolution
- Reseat NIC in PCIe slot
- Update BIOS/firmware
- Try different PCIe slot
- Check for thermal throttling
