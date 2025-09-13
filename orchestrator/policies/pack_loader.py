import requests, os, json

OPA_URL = os.getenv("OPA_URL", "http://opa:8181")

def load_tenant_pack(tenant_id: str, rego_bundle_path: str) -> bool:
    """Pushes a Rego module bundle to OPA under a tenant-specific package.

    This function reads a Rego bundle from the given path and pushes it to the
    Open Policy Agent (OPA) server under a tenant-specific package.

    Args:
        tenant_id: The ID of the tenant.
        rego_bundle_path: The path to the Rego bundle file.

    Returns:
        True if the bundle was loaded successfully, False otherwise.
    """
    with open(rego_bundle_path, "rb") as f:
        rego = f.read()
    # For a simple demo, we use OPA's bundle-like PUT to a policy path
    resp = requests.put(f"{OPA_URL}/v1/policies/tenant_{tenant_id}", data=rego, headers={"Content-Type":"text/plain"})
    return resp.status_code in (200, 204)
