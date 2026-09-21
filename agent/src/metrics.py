"""Prometheus metrics recorded by the agent worker.

LiveKit Agents runs every job in its own process, so a counter incremented
inside a job is invisible to a `start_http_server` in the parent. The worker is
therefore started with `prometheus_multiproc_dir` (see `agent.py`): each job
process writes its samples into that directory and the worker's `/metrics`
handler aggregates them with `MultiProcessCollector`.

The metric objects below are created at import time. In a job process the
`PROMETHEUS_MULTIPROC_DIR` environment variable is already set (the worker sets
it before spawning), so they land in the shared directory; in the parent they
are created but never recorded.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

#: Must match the directory created in `agent/Dockerfile` and be writable by
#: the container user.
PROMETHEUS_MULTIPROC_DIR = "/tmp/prometheus-multiproc"

#: Sourced from `ChatMessage.metrics["e2e_latency"]`, the SDK's measurement of
#: the gap between the learner finishing speaking and the tutor starting to
#: answer. The SDK reports seconds; this metric is milliseconds.
E2E_LATENCY_MS = Histogram(
    "voice_tutor_e2e_latency_ms",
    "End-to-end voice response latency in milliseconds",
    buckets=[100, 250, 350, 500, 750, 1000, 1500, 2000],
)

#: Incremented when an assistant turn is recorded with `interrupted=True`,
#: i.e. the learner barged in over the tutor.
INTERRUPTIONS = Counter(
    "voice_tutor_interruptions_total",
    "Barge-in interruptions of the tutor by the learner",
)

#: Tracked by the agent, which is the only component that knows a voice
#: session is actually running: up on job start, down on job shutdown.
#: `livesum` so the worker's /metrics reports the total across job processes
#: rather than one series per PID.
ACTIVE_SESSIONS = Gauge(
    "voice_tutor_active_sessions_total",
    "Voice tutoring sessions currently in progress",
    multiprocess_mode="livesum",
)
