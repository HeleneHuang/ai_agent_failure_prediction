# -*- coding: utf-8 -*-

import random
import datetime

# This module simulates collecting health metrics from storage nodes.
# In a real-world scenario, this would involve querying Prometheus, reading log files,
# or calling node-specific health check APIs.


def get_node_health(node: dict) -> dict:
    """
    Generates a simulated health report for a single node.
    The 'unstable' node is programmed to have a higher chance of showing warning signs.
    """
    is_unstable_node = "unstable" in node["id"]

    # Base metrics are mostly healthy
    health_report = {
        "node_id": node["id"],
        "timestamp_utc": datetime.datetime.utcnow().isoformat(),
        "disk_io_errors": 0,
        "network_packet_loss_rate": random.uniform(0.0, 0.01),
        "latency_p99_ms": random.randint(10, 50),
        "smart_warnings": 0,
        "checksum_mismatch_rate": random.uniform(0.0, 0.001),
        "raft_term_changes_per_hour": random.randint(0, 2),
        "available_disk_gb": random.randint(500, 4000),
    }

    # Introduce a higher probability of anomalies for the unstable node
    if is_unstable_node and random.random() < 0.6:  # 60% chance of showing some issue
        health_report["disk_io_errors"] = random.randint(1, 10)
        health_report["latency_p99_ms"] = random.randint(200, 1000)
        health_report["checksum_mismatch_rate"] = random.uniform(0.05, 0.2)
        if random.random() < 0.4:  # 40% chance of a more severe issue
            health_report["smart_warnings"] = random.randint(1, 5)

    # All nodes have a small chance of a random glitch
    elif random.random() < 0.05:  # 5% chance for any node
        health_report["latency_p99_ms"] = random.randint(100, 300)

    return health_report


def get_cluster_health(nodes: list) -> list:
    """
    Collects health reports for all nodes in the cluster.

    Args:
        nodes (list): A list of node dictionaries from the config.

    Returns:
        list: A list of health report dictionaries for each node.
    """
    print("🛰️  Monitoring: Collecting health metrics from all cluster nodes...")
    cluster_health_reports = [get_node_health(node) for node in nodes]
    print("✅ Monitoring: Collection complete.")
    return cluster_health_reports


if __name__ == "__main__":
    # Example of how to use this module directly for testing
    from config import CLUSTER_NODES

    print("--- Running Monitor Standalone Test ---")
    reports = get_cluster_health(CLUSTER_NODES)
    import json

    print(json.dumps(reports, indent=2))
    print("------------------------------------")
