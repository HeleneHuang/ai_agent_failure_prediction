# -*- coding: utf-8 -*-

import time
import copy

import config
import monitor
import predictor
import healer


class AIOpsAgent:
    def __init__(self):
        """Initializes the agent with the configuration."""
        print("--- AIOps Agent Initializing ---")
        self.current_nodes = copy.deepcopy(config.CLUSTER_NODES)
        self.greylisted_nodes = set()  # Track nodes in the warning state
        self.sleep_interval = config.AGENT_SLEEP_INTERVAL_SECONDS

        print(f"Monitoring {len(self.current_nodes)} nodes.")
        print(f"Check interval is set to {self.sleep_interval} seconds.")
        if config.LLM_CONFIG["use_mock"]:
            w_interval = config.LLM_CONFIG["mock_warning_prediction_interval"]
            c_interval = config.LLM_CONFIG["mock_critical_prediction_interval"]
            print("Running in MOCK mode. No real LLM API calls will be made.")
            print(
                f"Mocking a 'warning' at check >= {w_interval} and 'critical' at check >= {c_interval}."
            )
        else:
            print("Running in LIVE mode. Using real LLM API for prediction.")
        print("--- Agent Initialized and Running ---")

    def run(self):
        """The main loop of the AIOps agent."""
        while True:
            try:
                self.run_check_cycle()
            except KeyboardInterrupt:
                print("\n--- AIOps Agent Shutting Down ---")
                break
            except Exception as e:
                print(f"CRITICAL ERROR in main agent loop: {e}")
                print("Agent will sleep and retry.")

            print(
                f"\n--- Cycle finished. Sleeping for {self.sleep_interval} seconds. ---"
            )
            time.sleep(self.sleep_interval)

    def run_check_cycle(self):
        """Performs a single cycle of monitoring, prediction, and healing."""
        print("\n" + "=" * 50)
        print(f"Starting new check cycle at {time.ctime()}")

        health_reports = monitor.get_cluster_health(self.current_nodes)

        for report in health_reports:
            node_id = report["node_id"]
            prediction = predictor.predict_failure(report)
            severity = prediction.get("severity", "none")
            reason = prediction.get("reason", "No reason provided.")

            if severity == "critical":
                self._handle_critical_node(report, reason)
                # Stop checking other nodes in this cycle to focus on the critical failure
                break
            elif severity == "warning":
                self._handle_warning_node(report, reason)
            else:
                print(f"✅ Node '{node_id}' appears healthy.")
                if node_id in self.greylisted_nodes:
                    print(
                        f"      -> Node '{node_id}' has recovered and is now removed from the greylist."
                    )
                    self.greylisted_nodes.remove(node_id)

    def _handle_critical_node(self, report, reason):
        node_id = report["node_id"]
        print(f"🚨 CRITICAL: Failure predicted for node '{node_id}'!")
        print(f"   Reason: {reason}")

        failing_node_config = self._find_node_config(node_id)
        if not failing_node_config:
            return

        new_node = healer.handle_critical_failure(failing_node_config, reason)
        if new_node:
            print("Updating agent's cluster state after critical failure...")
            self.current_nodes = [n for n in self.current_nodes if n["id"] != node_id]
            self.current_nodes.append(new_node)
            # Remove from greylist if it was there
            self.greylisted_nodes.discard(node_id)
            self._print_cluster_state()

    def _handle_warning_node(self, report, reason):
        node_id = report["node_id"]
        print(f"⚠️ WARNING: Potential issue detected for node '{node_id}'.")
        print(f"   Reason: {reason}")

        node_config = self._find_node_config(node_id)
        if not node_config:
            return

        if node_id not in self.greylisted_nodes:
            # First time this node has a warning, add to greylist and expand cluster
            print(
                f"   -> Node '{node_id}' is not in greylist. Adding it and expanding cluster."
            )
            self.greylisted_nodes.add(node_id)
            new_node = healer.handle_greylist_expansion(node_config, reason)
            if new_node:
                print("Updating agent's cluster state after greylist expansion...")
                self.current_nodes.append(new_node)
                self._print_cluster_state()
        else:
            # Node is already in the greylist, just send a follow-up alert
            print(
                f"   -> Node '{node_id}' is already in greylist. Sending follow-up alert."
            )
            healer.send_alert(
                config.ALERTING_CONFIG["recipient_email"],
                node_id,
                reason,
                "warning",
                is_follow_up=True,
            )

    def _find_node_config(self, node_id):
        """Finds the full configuration dictionary for a given node ID."""
        node_config = next((n for n in self.current_nodes if n["id"] == node_id), None)
        if not node_config:
            print(f"Could not find config for node {node_id}. Cannot proceed.")
        return node_config

    def _print_cluster_state(self):
        """Prints the current list of nodes and greylisted nodes."""
        print("Current cluster state:")
        for node in self.current_nodes:
            status = "[GREYLISTED]" if node["id"] in self.greylisted_nodes else ""
            print(f"  - {node['id']} ({node['address']}) {status}")


if __name__ == "__main__":
    agent = AIOpsAgent()
    agent.run()
