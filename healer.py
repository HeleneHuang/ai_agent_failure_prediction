# -*- coding: utf-8 -*-

import subprocess
import time

from config import HEALER_CONFIG, ALERTING_CONFIG

# This module is responsible for taking action based on the predicted severity.
# It handles greylisting (expansion) and critical failures (replacement).

# A simple in-memory counter to ensure newly created nodes have unique addresses
_new_node_counter = 0

def send_alert(recipient_email: str, node_id: str, reason: str, severity: str, is_follow_up: bool = False):
    """
    Sends a failure alert with different content based on severity.
    """
    if not ALERTING_CONFIG["enabled"]:
        return

    if severity == "critical":
        subject = f"🚨 CRITICAL Alert: Immediate Replacement for Node {node_id}"
        action_taken = f"The agent has initiated a full replacement of node '{node_id}'."
    elif severity == "warning":
        if is_follow_up:
            subject = f"📢 FOLLOW-UP Alert: Node {node_id} Still in Greylist"
            action_taken = f"This is a follow-up alert. Node '{node_id}' remains in the greylist and is being monitored."
        else:
            subject = f"⚠️ WARNING Alert: Node {node_id} Added to Greylist"
            action_taken = f"The agent has added node '{node_id}' to the greylist and expanded the cluster to mitigate risk."
    else:
        return # Do not send alerts for 'none' severity

    body = f"""
Greetings System Administrator,

This is an automated alert from the AIOps Self-Healing Agent.

- **Severity:** {severity.upper()}
- **Node:** {node_id}
- **Reason:** {reason}
- **Action Taken:** {action_taken}

Please monitor the cluster's health.

- Your Trusty AI Assistant
    """
    print("\n--- Sending Alert ---")
    print(f"To: {recipient_email}")
    print(f"Subject: {subject}")
    print(body)
    print("--- Alert Sent ---\n")

def _provision_new_node() -> dict:
    """
    Simulates the creation of a new, healthy node.
    In a real cloud environment, this would involve calling the cloud provider's API
    (e.g., `boto3` for AWS to create an EC2 instance).
    """
    global _new_node_counter
    _new_node_counter += 1
    
    new_node_id = f"node-new-{int(time.time())}"
    new_node_addr = HEALER_CONFIG["new_node_address_template"].format(i=_new_node_counter)
    
    print(f"🔧 Healer: Provisioning new replacement node: {new_node_id} at {new_node_addr}")
    # Simulate time taken to provision
    time.sleep(2)
    print(f"✅ Healer: New node {new_node_id} is ready.")
    
    return {"id": new_node_id, "address": new_node_addr}

def _add_node_to_raft_cluster(new_node_addr: str):
    """
    Simulates adding the new node to the Raft consensus group.
    Replace the print statement with your system's actual command-line tool or API call.
    """
    print(f"🔧 Healer: Adding new node ({new_node_addr}) to the Raft cluster...")
    # --- REAL IMPLEMENTATION EXAMPLE ---
    # try:
    #     # Example: raft-tool add-peer <address>
    #     subprocess.run(
    #         ["your-raft-cli", "add-peer", new_node_addr],
    #         check=True, text=True, capture_output=True
    #     )
    # except subprocess.CalledProcessError as e:
    #     print(f"❌ Healer ERROR: Failed to add node to Raft cluster. Stderr: {e.stderr}")
    #     raise
    # -----------------------------------
    time.sleep(1)
    print(f"✅ Healer: New node ({new_node_addr}) successfully joined the Raft cluster.")

def _remove_node_from_raft_cluster(failing_node_addr: str):
    """
    Simulates removing the failing node from the Raft consensus group.
    Replace the print statement with your system's actual command-line tool or API call.
    """
    print(f"🔧 Healer: Removing failing node ({failing_node_addr}) from the Raft cluster...")
    # --- REAL IMPLEMENTATION EXAMPLE ---
    # try:
    #     # Example: raft-tool remove-peer <address>
    #     subprocess.run(
    #         ["your-raft-cli", "remove-peer", failing_node_addr],
    #         check=True, text=True, capture_output=True
    #     )
    # except subprocess.CalledProcessError as e:
    #     print(f"❌ Healer ERROR: Failed to remove node from Raft cluster. Stderr: {e.stderr}")
    #     raise
    # -----------------------------------
    time.sleep(1)
    print(f"✅ Healer: Failing node ({failing_node_addr}) successfully removed from the Raft cluster.")

def handle_greylist_expansion(node_info: dict, reason: str) -> dict:
    """
    Handles a 'warning' scenario: expands the cluster without removing the node.
    
    Returns:
        The new node that was created.
    """
    node_id = node_info["id"]
    print(f"\n--- Initiating Greylist Process for Node: {node_id} ---")
    
    send_alert(ALERTING_CONFIG["recipient_email"], node_id, reason, severity="warning")
    
    try:
        new_node = _provision_new_node()
        _add_node_to_raft_cluster(new_node["address"])
        print(f"✅ Greylist: Process completed for node {node_id}. Cluster expanded.")
        return new_node
    except Exception as e:
        print(f"❌ Greylist: Process FAILED for node {node_id}. Error: {e}")
        return None
    finally:
        print("--- Greylist Process Finished ---\n")

def handle_critical_failure(failing_node: dict, reason: str) -> dict:
    """
    Handles a 'critical' scenario: replaces the failing node.

    Returns:
        The new node that was created to replace the old one.
    """
    failing_node_id = failing_node["id"]
    failing_node_addr = failing_node["address"]
    
    print(f"\n--- Initiating Critical Replacement for Node: {failing_node_id} ---")
    
    send_alert(ALERTING_CONFIG["recipient_email"], failing_node_id, reason, severity="critical")
    
    try:
        new_node = _provision_new_node()
        _add_node_to_raft_cluster(new_node["address"])
        _remove_node_from_raft_cluster(failing_node_addr)
        
        print(f"✅ Critical: Replacement completed successfully for node {failing_node_id}.")
        return new_node
    except Exception as e:
        print(f"❌ Critical: Replacement FAILED for node {failing_node_id}. Error: {e}")
        return None
    finally:
        print("--- Critical Replacement Finished ---\n")

if __name__ == '__main__':
    print("\n--- Running Healer Standalone Test ---\n")
    
    # Test Greylist Scenario
    test_warning_node = {"id": "node-test-warn", "address": "192.168.1.98"}
    test_warn_reason = "This is a test of the greylist workflow."
    handle_greylist_expansion(test_warning_node, test_warn_reason)

    # Test Critical Scenario
    test_failing_node = {"id": "node-test-fail", "address": "192.168.1.99"}
    test_fail_reason = "This is a test of the critical failure workflow."
    handle_critical_failure(test_failing_node, test_fail_reason)
    
    print("------------------------------------") 