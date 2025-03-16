# app/probe.py
import subprocess
import json
import requests
import logging
from config import PROBE_CONFIG

# Your Discord webhook URL
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1343278754155335795/uCTv8j4Rh_6JNzs5x-C3jCitqhx3l6I9R2H4221vxxkvnE6tCCbpCe2Rft3gy9Bct-OC"

def run_command(cmd):
    """Runs a shell command and returns stdout."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        logging.debug(f"Command '{cmd}' output: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command '{cmd}' failed: {e.stderr.strip()}")
        return None

def get_all_pods():
    """Get all pods across all namespaces in JSON format."""
    cmd = f"{PROBE_CONFIG['kubectl_cmd']} get pods --all-namespaces -o json"
    output = run_command(cmd)
    if output:
        try:
            pods_json = json.loads(output)
            return pods_json.get("items", [])
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
    return []

# def check_pods():
#     """Check each pod’s status and return a list of pods that are not running."""
#     pods = get_all_pods()
#     failed_pods = []
#     for pod in pods:
#         phase = pod.get("status", {}).get("phase", "")
#         if phase != "Running":
#             ns = pod.get("metadata", {}).get("namespace", "default")
#             name = pod.get("metadata", {}).get("name", "unknown")
#             failed_pods.append({"namespace": ns, "name": name, "phase": phase})
#     return failed_pods

def check_pods():
    """Check each pod’s status and return a list of pods that are not running, ignoring probe pods in Pending/Completed state."""
    pods = get_all_pods()
    failed_pods = []
    for pod in pods:
        phase = pod.get("status", {}).get("phase", "")
        name = pod.get("metadata", {}).get("name", "unknown")
        ns = pod.get("metadata", {}).get("namespace", "default")

        # Ignore probe-microservice pods in Pending or Completed states
        if name.startswith("probe-microservice") and phase in ["Pending", "Completed"]:
            continue

        if phase != "Running":
            failed_pods.append({"namespace": ns, "name": name, "phase": phase})
    return failed_pods


def describe_and_get_logs(namespace, pod_name):
    """Run kubectl describe and logs for a given pod."""
    desc = run_command(f"{PROBE_CONFIG['kubectl_cmd']} describe pod {pod_name} -n {namespace}")
    logs = run_command(f"{PROBE_CONFIG['kubectl_cmd']} logs {pod_name} -n {namespace}")
    if logs is None:
        logs = "No logs available"
    return desc, logs

def extract_critical_error(desc):
    """
    Scan the 'kubectl describe' output for critical issues such as ephemeral storage errors.
    Returns a concise error message if found; otherwise returns an empty string.
    """
    if not desc:
        return ""
    lowered = desc.lower()
    keywords = ["ephemeral", "storage", "error"]
    for keyword in keywords:
        if keyword in lowered:
            # Extract the line containing the keyword
            for line in desc.splitlines():
                if keyword in line.lower():
                    return line.strip()
    return ""

def test_curl():
    """Send a POST request to the given URL with the specified payload."""
    url = PROBE_CONFIG["curl_url"]
    payload = PROBE_CONFIG["curl_payload"]
    try:
        response = requests.post(url, json=payload, timeout=PROBE_CONFIG["curl_timeout"])
        logging.info(f"Curl response code: {response.status_code}")
        if response.status_code == 200:
            return True, response.text
        else:
            return False, response.text
    except Exception as e:
        logging.error(f"Curl exception: {e}")
        return False, str(e)

def send_discord_alert(message):
    """Send an alert to a Discord channel via webhook."""
    payload = {"content": f"🚨 **ALERT:** {message}"}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("Discord alert sent successfully.")
        else:
            logging.error(f"Failed to send Discord alert: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Discord alert: {e}")

def run_probe():
    logging.info("Starting probe...")

    # 1. Check pods
    failed_pods = check_pods()
    if failed_pods:
        for pod in failed_pods:
            ns = pod["namespace"]
            name = pod["name"]
            phase = pod["phase"]
            desc, logs = describe_and_get_logs(ns, name)
            error_line = extract_critical_error(desc)
            if error_line:
                alert = f"Pod {name} in {ns} is failing due to: {error_line}"
            else:
                alert = f"Pod {name} in {ns} is not running (phase: {phase})."
            logging.error(alert)
            send_discord_alert(alert)
    else:
        logging.info("All pods are running.")

    # 2. Run the curl test
    curl_success, curl_response = test_curl()
    if curl_success:
        logging.info("Curl test passed. System appears healthy.")
    else:
        alert = ("Curl test failed! Please check backend logs at "
                 "https://monitoring.defendai.tech")
        logging.error(alert)
        send_discord_alert(alert)

if __name__ == "__main__":
    # In production, you may want to set logging level to WARNING to reduce log output.
    logging.basicConfig(
        level=logging.WARNING,  # Change to INFO/DEBUG during development
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    run_probe()
