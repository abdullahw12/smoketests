# app/config.py

# Example configuration for endpoints to check.
# (You can extend this if needed.)
PROBE_CONFIG = {
    "kubectl_cmd": "kubectl",
    "curl_url": "https://synergy.defendai.tech/wauzeway",
    "curl_payload": {
        "llm_type": "groq",
        "api_key": "489abc4d-e7be-46ed-a672-f387d99300cc",
        "llm_api_key": "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",
        "tenant_id": "synergy",
        "meta": {"model_name": "llama-3.1-8b-instant"},
        "prompt": "hey there"
    },
    # Define specific targets for additional diagnostics if curl fails.
    "diagnostic_targets": {
        "defendai-be": {"namespace": "default"},
        "waws": {"namespace": "waws"}
    },
    # Timeout settings (in seconds) for curl requests.
    "curl_timeout": 30
}
