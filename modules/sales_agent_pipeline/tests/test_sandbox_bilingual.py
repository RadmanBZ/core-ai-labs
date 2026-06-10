import pytest

from modules.sales_agent_pipeline.core.sandbox_engine import SandboxEngine


@pytest.mark.asyncio
async def test_persian_name_budget_and_pain_extraction():
    engine = SandboxEngine()
    history = [
        {
            "role": "user",
            "content": (
                "سلام، من رادمان هستم از آژانس املاک بیات‌زاده. "
                "نیاز به راه‌اندازی کال‌سنتر هوشمند داریم. بودجه ۵,۰۰۰ ریال عمان."
            ),
        }
    ]

    extracted = await engine.extract_lead_info(history)

    assert extracted.customer_name == "رادمان"
    assert extracted.company_name == "آژانس املاک"
    assert extracted.budget_range is not None
    assert "5,000" in extracted.budget_range
    assert extracted.primary_pain_point is not None
    assert "کال" in extracted.primary_pain_point or "هوش" in extracted.primary_pain_point


@pytest.mark.asyncio
async def test_persian_inbound_reply_is_farsi():
    engine = SandboxEngine()
    reply = await engine.generate_inbound_reply(
        "من رادمان هستم و برای کال‌سنتر هوشمند بودجه ۵۰۰۰ ریال عمان داریم.",
        [],
    )
    assert any("\u0600" <= ch <= "\u06FF" for ch in reply)
    assert "رایزا" in reply


@pytest.mark.asyncio
async def test_high_budget_scores_qualified():
    engine = SandboxEngine()
    history = [
        {
            "role": "user",
            "content": "I'm Ali from Muscat Logistics. Budget is 5,000 OMR for call center AI.",
        }
    ]

    extracted = await engine.extract_lead_info(history)
    evaluation = await engine.score_lead(extracted, history[0]["content"])
    status = engine.resolve_status(extracted, evaluation)

    assert evaluation.budget_fit >= 9
    assert status.value == "QUALIFIED"
