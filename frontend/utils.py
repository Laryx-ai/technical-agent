import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
_API_KEY = os.getenv("API_KEY", "").strip()


def _auth_headers() -> dict:
    """Return X-API-Key header when an API key is configured."""
    return {"X-API-Key": _API_KEY} if _API_KEY else {}


def api(method: str, path: str, **kwargs):
    url = f"{BACKEND_URL}{path}"
    headers = {**_auth_headers(), **kwargs.pop("headers", {})}
    try:
        resp = getattr(requests, method)(url, timeout=60, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to the backend. Make sure the server is running."
    except requests.exceptions.Timeout:
        return None, "The request timed out. The backend may be overloaded."
    except requests.exceptions.HTTPError as e:
        detail = ""
        try:
            detail = e.response.json().get("detail", "")
        except Exception:
            pass
        return None, f"Backend error ({e.response.status_code}): {detail or str(e)}"
    except Exception as e:
        return None, str(e)


def intent_badge(emoji: str, label: str) -> str:
    return f"{emoji} **{label}**"


def sidebar_agent_info():
    """Render agent identity block at the bottom of the sidebar. Returns the health info dict."""
    import streamlit as st
    info, err = api("get", "/health")
    kb_data, _ = api("get", "/kb/documents")
    kb_count = len((kb_data or {}).get("documents", []))

    # Status signals
    if info:
        backend_dot = "<span style='color:green'>&#9679;</span>"
        backend_label = "Backend &mdash; online"
    else:
        backend_dot = "<span style='color:red'>&#9679;</span>"
        backend_label = "Backend &mdash; offline"

    kb_dot = "<span style='color:green'>&#9679;</span>" if kb_count > 0 else "<span style='color:orange'>&#9679;</span>"
    kb_label = f"Knowledge base &mdash; {kb_count} doc{'s' if kb_count != 1 else ''}"

    st.sidebar.markdown(
        f"<small style='line-height:2'>"
        f"{backend_dot} {backend_label}<br>"
        f"{kb_dot} {kb_label}"
        f"</small>",
        unsafe_allow_html=True,
    )

    # Agent identity at the very bottom
    st.sidebar.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    if info:
        st.sidebar.caption(f"{info.get('agent', 'Support Agent')}  ·  {info.get('company', 'SaaS')}  ·  v{info.get('version', '2.0.0')}")
    else:
        st.sidebar.caption("Support Agent")
    return info
