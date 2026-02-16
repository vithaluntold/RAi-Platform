import json
import urllib.request

TOKEN_URL = "http://localhost:8000/api/v1/login/access-token"
AGENT_URL = "http://localhost:8000/api/v1/agents"

# Get token
data = "username=admin@rai-platform.com&password=Admin@123456"
req = urllib.request.Request(TOKEN_URL, data=data.encode(), headers={"Content-Type": "application/x-www-form-urlencoded"})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())["access_token"]
print(f"Token: {token[:20]}...")

# Create compliance agent
payload = {
    "name": "RAI Compliance Analysis Agent",
    "description": "Automated compliance checking of financial statements against IFRS/US GAAP/Ind AS standards using decision tree-driven chain-of-thought analysis.",
    "version": "4.0.0",
    "agent_type": "compliance_analysis",
    "provider_type": "external",
    "backend_provider": "azure",
    "external_url": "https://rai-compliance-analysis-production.up.railway.app",
    "backend_config": {
        "llm_endpoints": [
            {"endpoint_url": "https://region1.openai.azure.com", "api_key": "pk-1", "deployment_name": "gpt-52-chat", "api_version": "2024-10-21"},
            {"endpoint_url": "https://region2.openai.azure.com", "api_key": "pk-2", "deployment_name": "gpt-52-chat", "api_version": "2024-10-21"}
        ],
        "document_intelligence": {"endpoint": "https://doc-intel.cognitiveservices.azure.com", "api_key": "pk-doc"},
        "search": {"endpoint": "https://search.search.windows.net", "admin_key": "pk-search", "index_name": "compliance-docs"},
        "temperature": 0.0,
        "max_tokens": 16384
    },
    "capabilities": {
        "document_extraction": ["pdf", "docx"],
        "semantic_search": True,
        "compliance_analysis": True,
        "frameworks_supported": ["IFRS", "US GAAP", "Ind AS"],
        "max_standards": 44,
        "parallel_workers": 6
    },
    "input_schema": {
        "type": "object",
        "required": ["financial_statements_file", "notes_file"],
        "properties": {
            "financial_statements_file": {"type": "file"},
            "notes_file": {"type": "file"},
            "framework": {"type": "string"}
        }
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "compliance_items": {"type": "array"},
            "compliance_rate": {"type": "number"}
        }
    }
}

req = urllib.request.Request(
    AGENT_URL,
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print("\n=== Agent Created ===")
    print(json.dumps(result, indent=2, default=str))

    # Now validate config
    agent_id = result["id"]
    validate_url = f"{AGENT_URL}/{agent_id}/validate-config"
    req2 = urllib.request.Request(
        validate_url,
        data=b"",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        method="POST"
    )
    resp2 = urllib.request.urlopen(req2)
    validation = json.loads(resp2.read())
    print("\n=== Config Validation ===")
    print(json.dumps(validation, indent=2, default=str))

    # List agents with filter
    list_url = f"{AGENT_URL}?provider_type=external&agent_type=compliance_analysis"
    req3 = urllib.request.Request(
        list_url,
        headers={"Authorization": f"Bearer {token}"}
    )
    resp3 = urllib.request.urlopen(req3)
    agents = json.loads(resp3.read())
    print(f"\n=== Agents (external, compliance_analysis): {len(agents)} found ===")
    for a in agents:
        print(f"  - {a['name']} v{a['version']} [{a['provider_type']}:{a['backend_provider']}]")

except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")
