import streamlit as st
import os
import re

LOG_PATH = os.path.join(os.path.dirname(__file__), '../../backend/logs/app.log')

st.set_page_config(page_title="Logs — SaaS Support Agent", layout="wide")
st.title("Backend Logs")

_PARSE_RE = re.compile(
    r"^(?P<ts>[^|]+)\|\s*(?P<level>TRACE|DEBUG|INFO|SUCCESS|WARNING|ERROR|CRITICAL)\s*\|(?P<src>[^-]*)-\s*(?P<msg>.*)$"
)
_ROUTE_RE = re.compile(r"(/\w[\w/\-]*)")
_KV_RE = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_/-]*)=([^,]+)")

_LEVEL_COLORS = {
    "TRACE": "#6b7280",
    "DEBUG": "#3b82f6",
    "INFO": "#10b981",
    "SUCCESS": "#14b8a6",
    "WARNING": "#f59e0b",
    "ERROR": "#ef4444",
    "CRITICAL": "#b91c1c",
}

st.markdown(
    """
    <style>
      :root {
        --level-trace: #6b7280;
        --level-debug: #3b82f6;
        --level-info: #10b981;
        --level-success: #14b8a6;
        --level-warning: #f59e0b;
        --level-error: #ef4444;
        --level-critical: #b91c1c;
      }
      .log-wrap { display:flex; flex-direction:column; gap:10px; margin-top:10px; }
      .log-row {
        --accent: #d1d5db;
        border: 1px solid var(--level-color, #d1d5db);
        border-radius:12px;
        padding:10px 12px;
        background: var(--level-success);
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
        font-size:12px;
        white-space: pre-wrap;
        word-break: break-word;
      }
      .log-head {
        display:flex;
        align-items:center;
        flex-wrap:wrap;
        gap:6px;
      }
      .log-badge {
        display:inline-block;
        padding:2px 8px;
        border-radius:500px;
        color:#fff;
        font-size:11px;
        font-weight:700;
      }
      .log-route {
        display:inline-block;
        margin-left:2px;
        padding:1px 7px;
        border-radius:500px;
        background: linear-gradient(180deg, #ecfeff 0%, #cffafe 100%);
        color:#0e7490;
        font-size:11px;
        font-weight:700;
      }
      .log-time {
        color:#6b7280;
        padding:1px 0;
      }
      .log-meta { color:#4b5563; }
      .log-msg {
        margin-top:8px;
        color:#111827;
        line-height:1.45;
      }
      .level-trace { --accent: var(--level-trace); }
      .level-debug { --accent: var(--level-debug); }
      .level-info { --accent: var(--level-info); }
      .level-success { --accent: var(--level-success); }
      .level-warning { --accent: var(--level-warning); }
      .level-error { --accent: var(--level-error); }
      .level-critical { --accent: var(--level-critical); }
      .log-row.level-trace,
      .log-row.level-debug,
      .log-row.level-info,
      .log-row.level-success,
      .log-row.level-warning,
      .log-row.level-error,
      .log-row.level-critical {
        border-left-color: var(--accent);
      }
      .log-badge.level-trace,
      .log-badge.level-debug,
      .log-badge.level-info,
      .log-badge.level-success,
      .log-badge.level-warning,
      .log-badge.level-error,
      .log-badge.level-critical {
        background: var(--accent);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def _parse_log_line(line: str) -> dict:
    match = _PARSE_RE.match(line)
    if not match:
        return {
            "timestamp": "",
            "level": "INFO",
            "source": "",
            "message": line,
            "route": "",
        }

    message = match.group("msg").strip()
    route_match = _ROUTE_RE.search(message)
    route = route_match.group(1) if route_match else ""
    return {
        "timestamp": match.group("ts").strip(),
        "level": match.group("level").strip(),
        "source": match.group("src").strip(),
        "message": message,
        "route": route,
    }


def _format_log_message(msg: str) -> str:
    title = msg
    payload = msg
    if ":" in msg:
        left, right = msg.split(":", 1)
        title = left.strip()
        payload = right.strip()

    pairs = _KV_RE.findall(payload)
    if not pairs:
        return f"**{title}**\n\n{payload if payload else msg}"

    lines = [f"**{title}**", ""]
    for key, value in pairs:
        clean_val = value.strip().replace("`", "'")
        lines.append(f"- `{key}`: {clean_val}")
    return "\n".join(lines)


if not os.path.exists(LOG_PATH):
    st.warning("Log file not found. Trigger some backend actions to generate logs.")
else:
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]

    if not lines:
        st.info("No log entries yet.")
    else:
        parsed = [_parse_log_line(line) for line in lines]
        recent = parsed[-50:]
        recent_errors = sum(1 for row in recent if row["level"] in ("ERROR", "CRITICAL"))
        recent_warnings = sum(1 for row in recent if row["level"] == "WARNING")

        if recent_errors > 0:
            st.error(f"Recent log health: {recent_errors} error/critical entries in the last {len(recent)} logs.")
        elif recent_warnings > 0:
            st.warning(f"Recent log health: {recent_warnings} warning entries in the last {len(recent)} logs.")
        else:
            st.success(f"Recent log health: no warnings or errors in the last {len(recent)} logs.")

        data = list(reversed(parsed[-250:]))

        for row in data:
            level = row["level"]
            ts = row["timestamp"]
            src = row["source"]
            msg = row["message"]
            route = row["route"]
            route_txt = f" [{route}]" if route else ""
            line = f"`{ts}`  `{src}`{route_txt}\n\n{_format_log_message(msg)}"

            if level in ("ERROR", "CRITICAL"):
                st.error(line)
            elif level == "WARNING":
                st.warning(line)
            elif level == "SUCCESS":
                st.success(line)
            else:
                st.info(line)
