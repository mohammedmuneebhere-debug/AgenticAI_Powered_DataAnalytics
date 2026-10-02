"""Phase 3 planner tests - concurrent stages with timeout + failure isolation.

The pipeline runs against fake data/LLM agents, so these tests assert
scheduling behavior (overlap, isolation, timeout) with no network, LLM or
database dependency.
"""

import asyncio
import time

from agents.master.planner import MasterAgent


RECORDS = [
    {
        "id": f"r{index}",
        "platform": "x",
        "text": f"Solar panel update {index} #energy",
        "author": f"@user{index % 3}",
        "timestamp": "2026-09-30T12:00:00+00:00",
        "engagement": {"likes": index, "reposts": 1},
    }
    for index in range(6)
]


def _master_with_fakes(social, domain):
    """MasterAgent whose data, LLM and synthetic stages are instant fakes."""
    master = MasterAgent()

    class FakeData:
        async def acquire(self, **kwargs):
            return {"records": list(RECORDS), "platforms": ["x"], "live_sources": []}

        async def web_search(self, *args, **kwargs):
            return []

    class FakeIntelligence:
        async def process(self, raw):
            return {"records": list(RECORDS), "snapshot": {"live_sources": []}}

    class FakeViz:
        async def generate(self, *args, **kwargs):
            return []

    class FakeInsight:
        async def generate(self, **kwargs):
            return {"text": "Synthetic test insight", "confidence": 0.8}

    class FakeSynthetic:
        async def fill_gaps(self, **kwargs):
            return {"sections": {}, "synthetic_posts": [], "disclosure": None}

    master.data_agent = FakeData()
    master.intelligence_agent = FakeIntelligence()
    master.viz_agent = FakeViz()
    master.insight_agent = FakeInsight()
    master.synthetic_agent = FakeSynthetic()
    master.social_agent = social
    master.domain_agent = domain
    return master


class _TimedAgent:
    """Records the wall-clock window of its analyze() call."""

    def __init__(self, name, window, result=None, raises=False, delay=0.15):
        self.name = name
        self.window = window
        self.result = result or {}
        self.raises = raises
        self.delay = delay

    async def analyze(self, *args, **kwargs):
        start = time.monotonic()
        await asyncio.sleep(self.delay)
        self.window.append((self.name, start, time.monotonic()))
        if self.raises:
            raise RuntimeError(f"{self.name} exploded")
        return dict(self.result)


def test_social_and_domain_stages_overlap():
    window = []
    social = _TimedAgent("social", window, result={"sentiment": {"overall_label": "positive"}})
    domain = _TimedAgent("domain", window, result={"volatility": {"level": "high"}})

    async def run():
        master = _master_with_fakes(social, domain)
        # financial/market intent so the domain analytics stage actually runs
        return await master.plan_and_execute("btc price volatility outlook")

    result = asyncio.run(run())

    assert len(window) == 2, "both analytics stages should have run"
    social_window = next(w for w in window if w[0] == "social")
    domain_window = next(w for w in window if w[0] == "domain")
    # Concurrency => the two execution windows overlap in time
    assert social_window[1] < domain_window[2] and domain_window[1] < social_window[2]
    assert result["analytics"]["sentiment"]["overall_label"] == "positive"
    assert result["analytics"]["_active_domain"] == "financial"


def test_failing_stage_isolates_and_others_survive():
    window = []
    social = _TimedAgent("social", window, raises=True)
    domain = _TimedAgent("domain", window, result={"volatility": {"level": "high"}})

    async def run():
        master = _master_with_fakes(social, domain)
        return await master.plan_and_execute("btc price volatility outlook")

    result = asyncio.run(run())

    # The exploded stage contributes nothing, but the response is still built
    assert "sentiment" not in result["analytics"]
    assert result["analytics"]["volatility"]["level"] == "high"
    assert result["response"].startswith("Synthetic test insight")


def test_stage_timeout_degrades_to_empty(monkeypatch):
    import backend.config as config

    class SlowAgent:
        async def analyze(self, *args, **kwargs):
            await asyncio.sleep(5)
            return {"never": True}

    async def run():
        master = _master_with_fakes(SlowAgent(), _TimedAgent("domain", [], result={"ok": 1}))
        return await master.plan_and_execute("btc price volatility outlook")

    settings = config.get_settings()
    monkeypatch.setattr(settings, "agent_timeout_seconds", 0.05, raising=False)
    result = asyncio.run(run())

    assert "never" not in result["analytics"]


def test_run_stage_passes_through_success():
    master = MasterAgent()

    async def ok():
        return {"value": 7}

    assert asyncio.run(master._run_stage("ok", ok())) == {"value": 7}
