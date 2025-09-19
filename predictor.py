# -*- coding: utf-8 -*-

import os
import json
import random

# Attempt to import the openai library. If it fails, the agent will
# automatically fall back to mock mode.
try:
    import openai  # Using the official openai library v0.28
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from config import LLM_CONFIG

# This module is the brain of the AI agent. It takes health metrics,
# formats them into a prompt, and queries an LLM to get a failure prediction.

# A counter to help the mock predictor simulate periodic failures
_mock_check_counter = 0

def _configure_openai_api():
    """Configures the OpenAI client for version 0.28."""
    openai.api_key = LLM_CONFIG["api_key"]
    # The base_url parameter is called api_base in v0.28
    if LLM_CONFIG.get("api_base_url") and "openai.com" not in LLM_CONFIG["api_base_url"]:
         openai.api_base = LLM_CONFIG["api_base_url"]

def predict_failure(node_health_report: dict) -> dict:
    """
    Predicts node failure using either a real LLM or a mock response.

    Args:
        node_health_report (dict): The health metrics for a single node.

    Returns:
        dict: A dictionary with 'severity' and 'reason'.
    """
    node_id = node_health_report["node_id"]
    print(f"🧠 Predictor: Analyzing health report for node '{node_id}'...")

    # Force mock mode if the openai library is not installed
    use_mock = LLM_CONFIG["use_mock"]
    if not OPENAI_AVAILABLE and not use_mock:
        print("⚠️  WARNING: 'openai' library not found. Forcing MOCK mode.")
        print("   To enable real LLM predictions, please run: pip3 install -r requirements.txt")
        use_mock = True

    if use_mock:
        return _predict_mock(node_health_report)

    try:
        _configure_openai_api()
        prompt = _build_llm_prompt_for_severity(node_health_report)
        
        # v0.28 uses openai.ChatCompletion.create
        chat_completion = openai.ChatCompletion.create(
            model=LLM_CONFIG["model_name"],
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert AIOps analysis engine. Respond in JSON.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
        )
        
        response_content = chat_completion.choices[0].message['content']
        try:
            prediction = json.loads(response_content)
        except json.JSONDecodeError:
            print(f"❌ Predictor ERROR: LLM did not return valid JSON. Response was:\n{response_content}")
            return {"severity": "none", "reason": "Prediction failed due to invalid LLM response format."}

        print(f"✅ Predictor: LLM analysis complete for node '{node_id}'.")
        return prediction

    except openai.error.APIConnectionError as e:
        print(f"❌ Predictor ERROR: Failed to connect to API: {e}")
    except openai.error.RateLimitError as e:
        print(f"❌ Predictor ERROR: Rate limit exceeded: {e}")
    except openai.error.AuthenticationError as e:
        print(f"❌ Predictor ERROR: Authentication failed. Check your API key. Error: {e}")
    except Exception as e:
        print(f"❌ Predictor ERROR: An unexpected error occurred: {e}")
    
    return {"severity": "none", "reason": "Prediction failed due to an API error."}

def _build_llm_prompt_for_severity(node_health_report: dict) -> str:
    """
    Creates a prompt that asks the LLM to classify the failure risk into different severity levels.
    """
    report_json_str = json.dumps(node_health_report, indent=2)
    
    prompt = f"""
You are an expert AIOps agent responsible for maintaining a distributed storage cluster.
Analyze the following health metrics from node '{node_health_report['node_id']}'.

**Node Health Metrics:**
```json
{report_json_str}
```

**Analysis Guidelines & Severity Levels:**
- **`none`**: All metrics are normal.
- **`warning`**: The node shows early signs of trouble but is still operational. This is for concerning but non-critical patterns.
    - `latency_p99_ms` between 150ms and 400ms.
    - A small, non-zero number of `disk_io_errors` (e.g., 1-10).
    - `checksum_mismatch_rate` is low but non-zero (e.g., < 0.01).
- **`critical`**: The node is at imminent risk of failure and requires immediate replacement.
    - Any `smart_warnings` > 0.
    - `disk_io_errors` are high (e.g., > 10).
    - `latency_p99_ms` is consistently high (e.g., > 400ms).
    - `checksum_mismatch_rate` is significant (e.g., >= 0.01).

**Your Response:**
Respond with a JSON object ONLY. The JSON object must have two keys:
1. `severity` (string): Your classification, which must be one of "none", "warning", or "critical".
2. `reason` (string): A brief, technical explanation for your decision.

Now, analyze the provided metrics and give your verdict.
"""
    return prompt

def _predict_mock(node_health_report: dict) -> dict:
    """A mock function that simulates an LLM's response with severity levels."""
    global _mock_check_counter
    _mock_check_counter += 1
    
    node_id = node_health_report["node_id"]
    is_unstable_node = "unstable" in node_id

    if not is_unstable_node:
        return {"severity": "none", "reason": "Mock: Node is stable."}

    # Simulate a progression from warning to critical for the unstable node
    warning_interval = LLM_CONFIG["mock_warning_prediction_interval"]
    critical_interval = LLM_CONFIG["mock_critical_prediction_interval"]

    if _mock_check_counter >= critical_interval:
        print(f" MOCK: Simulating a 'critical' prediction for '{node_id}'.")
        return {
            "severity": "critical",
            "reason": f"Mock critical failure: Node '{node_id}' is showing multiple critical signs (e.g., S.M.A.R.T. warnings)."
        }
    elif _mock_check_counter >= warning_interval:
        print(f" MOCK: Simulating a 'warning' prediction for '{node_id}'.")
        return {
            "severity": "warning",
            "reason": f"Mock warning: Node '{node_id}' is showing early signs of trouble (e.g., elevated latency)."
        }
    else:
        print(f" MOCK: Simulating a 'none' prediction for '{node_id}'.")
        return {"severity": "none", "reason": "Mock: Unstable node is currently healthy."}

if __name__ == '__main__':
    from config import CLUSTER_NODES
    
    print("\n--- Running Predictor Standalone Test (Mocked Severity) ---\n")
    LLM_CONFIG["use_mock"] = True
    unstable_node_report = {"id": "node-4-unstable", "address": "..."}
    
    _mock_check_counter = 0
    print(f"Check 1: {json.dumps(predict_failure(unstable_node_report), indent=2)}")
    
    _mock_check_counter = LLM_CONFIG["mock_warning_prediction_interval"] -1
    print(f"Check {LLM_CONFIG['mock_warning_prediction_interval']}: {json.dumps(predict_failure(unstable_node_report), indent=2)}")

    _mock_check_counter = LLM_CONFIG["mock_critical_prediction_interval"] -1
    print(f"Check {LLM_CONFIG['mock_critical_prediction_interval']}: {json.dumps(predict_failure(unstable_node_report), indent=2)}")
    print("------------------------------------") 