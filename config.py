# -*- coding: utf-8 -*-

import os

# --- Agent Configuration ---
# The main loop of the agent will sleep for this many seconds between checks
AGENT_SLEEP_INTERVAL_SECONDS = 15

# --- Cluster Configuration ---
# A list of node identifiers that the agent will monitor.
# In a real system, these would be hostnames or IP addresses.
CLUSTER_NODES = [
    {"id": "node-1", "address": "192.168.1.101"},
    {"id": "node-2", "address": "192.168.1.102"},
    {"id": "node-3", "address": "192.168.1.103"},
    # This node is programmed to be more likely to fail for demonstration purposes
    {"id": "node-4-unstable", "address": "192.168.1.104"},
]

# --- LLM Predictor Configuration ---
LLM_CONFIG = {
    # Set to False to use a real LLM API.
    # If True, the predictor will use a mock response and simulate a failure
    # prediction every MOCK_FAILURE_PREDICTION_INTERVAL checks.
    "use_mock": True,
    # This is a placeholder for your actual LLM API key.
    # It's recommended to load this from an environment variable for security.
    # e.g., os.getenv("OPENAI_API_KEY")
    "api_key": "YOUR_LLM_API_KEY_HERE",
    # The specific model you want to use. This could be "gpt-4", "claude-3-opus-20240229", etc.
    "model_name": "gpt-4-turbo",
    # The base URL of the API. For OpenAI, it's "https://api.openai.com/v1".
    # This can be changed to use other providers or self-hosted models.
    "api_base_url": "https://api.openai.com/v1",
    # --- Mock Behavior ---
    # The mock predictor will trigger a 'warning' status when the check counter
    # reaches this value.
    "mock_warning_prediction_interval": 3,
    # The mock predictor will trigger a 'critical' status when the check counter
    # reaches this value. It should be greater than the warning interval.
    "mock_critical_prediction_interval": 5,
}


# --- Self-Healing Configuration ---
HEALER_CONFIG = {
    # A template for generating new node addresses. The "{i}" will be replaced
    # with an incrementing number to ensure uniqueness.
    "new_node_address_template": "192.168.1.20{i}"
}


# --- Alerting Configuration ---
ALERTING_CONFIG = {
    "enabled": True,
    # The email address to which failure alerts will be sent.
    "recipient_email": "admin@distributedsystem.com",
}
