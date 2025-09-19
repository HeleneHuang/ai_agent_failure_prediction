# AI Agent for Predictive Failure & Self-Healing

This module implements an AI Agent designed to predict potential failures in a distributed storage system and perform automated self-healing actions. It is a practical application of AIOps, leveraging a Large Language Model (LLM) to analyze system health and trigger proactive recovery procedures.

## Core Features

- **Simulated Health Monitoring**: Continuously generates realistic health metrics for a cluster of storage nodes.
- **LLM-Powered Failure Prediction**: Utilizes an external LLM (e.g., GPT-4, Claude) to analyze health data and classify node status into `none`, `warning`, or `critical`.
- **Two-Tiered Self-Healing**:
    - **Greylist (`warning`)**: If a node shows early warning signs, it is added to a "greylist." The agent **expands the cluster** by adding a new node but **does not remove** the greylisted node, while sending continuous alerts.
    - **Critical Failure (`critical`)**: If a node is predicted to fail imminently, the agent **replaces it** by adding a new node and then removing the faulty one.
- **Alerting**: Includes a placeholder for sending email alerts to administrators.
- **Mockable & Extensible**: Designed with a mock mode for testing without a real LLM API key.

## Project Structure

```
ai_agent_failure_prediction/
├── agent.py                # Main control loop for the agent
├── predictor.py            # Handles interaction with the LLM for prediction
├── healer.py               # Implements the self-healing logic (greylist and critical)
├── monitor.py              # Simulates the collection of node health metrics
├── config.py               # All configurations (nodes, API keys, etc.)
├── requirements.txt        # Python dependencies
└── README.md               # This documentation file
```

## Installation and Configuration

### 1. Install Dependencies

It is highly recommended to use Python 3.7 or newer. The primary dependency is the `openai` library.

```bash
# Navigate to the project root directory
pip3 install -r ai_agent_failure_prediction/requirements.txt
```

**Troubleshooting:**
- If the command fails, you might be using an old version of Python or `pip`. The `openai==0.28` library requires Python 3.7+.
- If you see `pip: command not found`, your system likely uses `pip3` for Python 3.
- If you are in a restricted environment (like some corporate networks or older OS versions), `pip3` might not be able to find the package. You may need to configure `pip` to use a different package index.

### 2. Configure the Agent

Open `ai_agent_failure_prediction/config.py` to set up your agent.

- **Mock Mode (for testing)**:
  - Keep `LLM_CONFIG["use_mock"] = True`.
  - The agent will use the `_predict_mock` function in `predictor.py`. It will not make any external API calls.
  - You can configure the mock behavior with `mock_warning_prediction_interval` and `mock_critical_prediction_interval`.

- **Live Mode (with a real LLM)**:
  - Set `LLM_CONFIG["use_mock"] = False`.
  - Provide your LLM API key in `LLM_CONFIG["api_key"]`. It is strongly recommended to load this from an environment variable for security.
  - Specify the model you want to use in `LLM_CONFIG["model_name"]` (e.g., `"gpt-4-turbo"`).
  - If you are using a provider other than OpenAI, you may need to change `LLM_CONFIG["api_base_url"]`.

- **Alerting**:
  - Set the administrator email in `ALERTING_CONFIG["recipient_email"]`.

## How to Run

Once configured, start the agent from the project's root directory:

```bash
python3 ai_agent_failure_prediction/agent.py
```

The agent will start its monitoring loop. Observe the console output to see the health checks, predictions, and any self-healing actions taken.

## Integration with Your Project

To integrate this agent with your actual distributed storage system, you would need to:

1.  **Replace `monitor.py`**: Modify the `get_cluster_health()` function to collect real metrics from your storage nodes' APIs or log files.
2.  **Implement `healer.py`**: Replace the `print` statements in the `initiate_self_healing` function with actual shell commands or API calls to your system's control plane to add/remove nodes from the Raft group.
    - Example: `subprocess.run(["your_cli_tool", "raft", "add-member", "--node-addr", new_node_addr])`
3.  **Implement `alert.py`**: Implement the `send_alert` function to use a real email service like SendGrid or AWS SES. 