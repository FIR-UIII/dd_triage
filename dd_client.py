import requests
import urllib3
from config import DD_URL, DD_API_KEY, DD_TIMEOUT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _headers():
    return {
        "Authorization": f"Token {DD_API_KEY}",
        "Content-Type": "application/json",
    }


def get_finding(finding_id: int) -> dict:
    url = f"{DD_URL}/api/v2/findings/{finding_id}/"
    resp = requests.get(url, headers=_headers(), timeout=DD_TIMEOUT, verify=False)
    resp.raise_for_status()
    data = resp.json()
    return data


def get_notes(finding_id: int) -> list:
    """Fetch paginated notes for a finding."""
    url = f"{DD_URL}/api/v2/notes/"
    params = {"finding": finding_id, "limit": 100}
    resp = requests.get(url, headers=_headers(), params=params, timeout=DD_TIMEOUT, verify=False)
    if not resp.ok:
        return []
    payload = resp.json()
    return payload.get("results", payload) if isinstance(payload, dict) else payload


def close_as_false_positive(finding_id: int) -> dict:
    url = f"{DD_URL}/api/v2/findings/{finding_id}/"
    resp = requests.patch(
        url,
        json={"false_p": True, "active": False},
        headers=_headers(),
        timeout=DD_TIMEOUT,
        verify=False
    )
    resp.raise_for_status()
    return resp.json()


def add_note(finding_id: int, entry: str) -> dict:
    url = f"{DD_URL}/api/v2/findings/{finding_id}/notes/"
    resp = requests.post(
        url,
        json={"entry": entry},
        headers=_headers(),
        timeout=DD_TIMEOUT,
        verify=False
    )
    resp.raise_for_status()
    return resp.json()
