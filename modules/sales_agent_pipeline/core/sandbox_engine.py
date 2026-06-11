import asyncio
import re
from typing import Dict, List, Optional, Tuple

from modules.sales_agent_pipeline.models import (
    ExtractedLeadInfo,
    LeadScoreMetadata,
    LeadStatus,
)

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

_EN_BUDGET_PATTERN = re.compile(
    r"(?:(?:budget|spend|allocate[d]?|around|approximately|~)\s*(?:of|is|:)?\s*)?"
    r"((?:OMR|USD|\$|€|£)\s*[\d,]+(?:\.\d+)?[KkMm]?|[\d,]+(?:\.\d+)?\s*(?:OMR|USD|Rial))",
    re.IGNORECASE,
)
_FA_BUDGET_PATTERN = re.compile(
    r"([\d۰-۹٠-٩,]+)\s*(ریال(?:\s*عمان)?|OMR|دلار|تومان|USD)",
    re.IGNORECASE,
)
_EN_TIMELINE_PATTERN = re.compile(
    r"(Q[1-4]\s*\d{4}|\d+\s*(?:days?|weeks?|months?)|within\s+\d+\s*(?:days?|weeks?|months?)|"
    r"next\s+quarter|this\s+quarter|ASAP|immediately)",
    re.IGNORECASE,
)
_FA_TIMELINE_PATTERN = re.compile(
    r"(فصل\s*(?:اول|دوم|سوم|چهارم)|سه\s*ماهه|ماه\s*آینده|هفته\s*آینده|فوری|هر\s*چه\s*سریعتر|Q[1-4])",
    re.IGNORECASE,
)
_EN_NAME_PATTERN = re.compile(
    r"(?:i(?:'m| am)\s+)([A-Za-z]+(?:[\s\-][A-Za-z]+)*)|"
    r"(?:my name is\s+)([A-Za-z]+(?:[\s\-][A-Za-z]+)*)|"
    r"(?:this is\s+)([A-Za-z]+(?:[\s\-][A-Za-z]+)*)",
    re.IGNORECASE,
)
_FA_NAME_PATTERN = re.compile(
    r"من\s+(.+?)\s+هستم|نام\s+من\s+(.+?)(?:\s+است|[\.،,]|$)",
)
_FA_SHORT_INTRO_PATTERN = re.compile(
    r"(?:^|[\s،,.])([\u0600-\u06FF]{2,24})\s+هستم",
)
_FA_GREETING_NAME_PATTERN = re.compile(
    r"(?:درود|سلام)[،,\s]+([\u0600-\u06FF]{2,30})",
)
_INTRODUCTION_MARKER_PATTERN = re.compile(
    r"(?:من\s+.+?\s+هستم|.+?\s+هستم|نام\s+من\b|"
    r"my name is\b|i(?:'m| am)\b|this is\b|"
    r"درود[،,\s]|سلام[،,\s])",
    re.IGNORECASE,
)
_EN_COMPANY_PATTERN = re.compile(
    r"(?:we(?:'re| are)\s+)([A-Za-z0-9\s&]+?)(?:\s*[—\-–,]|\.|\s+(?:and|looking|need|want|our)\b)|"
    r"(?:at\s+)([A-Za-z0-9\s&]+?)(?:\s*[—\-–,]|\.|\s+(?:and|looking|need|want)\b)|"
    r"(?:from\s+)([A-Za-z0-9\s&]+?)(?:\s*[—\-–,]|\.|\s+(?:and|looking|need|want)\b)",
    re.IGNORECASE,
)
_FA_COMPANY_PATTERN = re.compile(
    r"(آژانس\s+املاک|کال[\s\-]*سنتر|شرکت\s+[\u0600-\u06FF\s]+|مجموعه\s+[\u0600-\u06FF\s]+|"
    r"از\s+([\u0600-\u06FF\s]{3,40}))",
)

_PAIN_CATALOG: Tuple[Tuple[str, str, str], ...] = (
    ("کال‌سنتر", "Smart AI-powered call center deployment", "راه‌اندازی کال‌سنتر هوشمند مجهز به هوش مصنوعی"),
    ("کال سنتر", "Smart AI-powered call center deployment", "راه‌اندازی کال‌سنتر هوشمند مجهز به هوش مصنوعی"),
    ("آژانس املاک", "Real estate agency digital automation", "اتوماسیون و دیجیتال‌سازی آژانس املاک"),
    ("هوش مصنوعی", "Enterprise AI integration initiative", "یکپارچه‌سازی راهکارهای هوش مصنوعی سازمانی"),
    ("invoice", "Manual invoice ingestion latency", "تأخیر در پردازش دستی فاکتورها"),
    ("manual", "Manual operational workflow bottlenecks", "گلوگاه‌های عملیاتی دستی"),
    ("automation", "Business process automation requirements", "نیاز به اتوماسیون فرآیندهای کسب‌وکار"),
    ("chatbot", "Customer support automation exploration", "بررسی اتوماسیون پشتیبانی مشتری"),
    ("call center", "Call center modernization program", "نوسازی زیرساخت کال‌سنتر"),
)

_FA_AUTHORITY_SIGNALS = (
    "مدیر", "رئیس", "صاحب", "بنیانگذار", "مالک", "مدیرعامل", "هیئت مدیره",
)
_NON_NAME_TOKENS = frozenset(
    {
        "دوباره",
        "وقت",
        "خوب",
        "برخی",
        "دوستان",
        "همکاران",
        "خدمت",
        "شما",
        "دوست",
        "عزیز",
    }
)
_EN_AUTHORITY_SIGNALS = (
    "head of", "director", "cto", "ceo", "vp", "sign off", "decision maker", "i approve",
)


def _normalize_digits(text: str) -> str:
    return text.translate(_PERSIAN_DIGITS).translate(_ARABIC_DIGITS)


def _is_persian(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text))


def _conversation_text(history: List[Dict[str, str]]) -> str:
    return " ".join(msg["content"] for msg in history if msg.get("content"))


def _latest_user_message(history: List[Dict[str, str]], user_message: str) -> str:
    return user_message or next(
        (msg["content"] for msg in reversed(history) if msg.get("role") == "user" and msg.get("content")),
        "",
    )


def has_introduction_marker(text: str) -> bool:
    """Detect whether a message contains an explicit self-introduction signal."""
    return bool(_INTRODUCTION_MARKER_PATTERN.search(text))


def extract_customer_identity(text: str) -> Optional[str]:
    """Public helper for detecting a lead name from a single inbound message."""
    return _extract_name(text)


def _clean_person_name(name: str) -> Optional[str]:
    cleaned = re.sub(r"\s+و\s+.*$", "", name.strip())
    cleaned = cleaned.strip("،,. ").strip()
    if not cleaned or len(cleaned) < 2:
        return None
    if cleaned in _NON_NAME_TOKENS:
        return None
    return cleaned[:60]


def _extract_name(text: str) -> Optional[str]:
    fa_match = _FA_NAME_PATTERN.search(text)
    if fa_match:
        return _clean_person_name(fa_match.group(1) or fa_match.group(2) or "")

    short_fa_match = _FA_SHORT_INTRO_PATTERN.search(text)
    if short_fa_match:
        return _clean_person_name(short_fa_match.group(1))

    greeting_match = _FA_GREETING_NAME_PATTERN.search(text)
    if greeting_match:
        candidate = greeting_match.group(1).strip()
        candidate = re.split(r"\s+و\s+|\s+از\s+", candidate)[0]
        return _clean_person_name(candidate)

    en_match = _EN_NAME_PATTERN.search(text)
    if en_match:
        return _clean_person_name(
            en_match.group(1) or en_match.group(2) or en_match.group(3) or ""
        )

    en_fallback = re.search(
        r"(?:i(?:'m| am)\s+)([A-Za-z]+(?:[\s\-][A-Za-z]+)*)",
        text,
        re.IGNORECASE,
    )
    if en_fallback:
        return _clean_person_name(en_fallback.group(1))

    return None


def _extract_budget(text: str) -> Optional[str]:
    normalized = _normalize_digits(text)

    fa_match = _FA_BUDGET_PATTERN.search(text) or _FA_BUDGET_PATTERN.search(normalized)
    if fa_match:
        amount = _normalize_digits(fa_match.group(1)).replace(",", "")
        currency = fa_match.group(2).strip()
        if "ریال" in currency and "عمان" in currency:
            return f"{int(amount):,} OMR (ریال عمان)"
        if "ریال" in currency:
            return f"{int(amount):,} ریال"
        return f"{int(amount):,} {currency}"

    en_match = _EN_BUDGET_PATTERN.search(normalized)
    if en_match:
        return en_match.group(1).strip()

    loose = re.search(
        r"([\d,]+)\s*(OMR|USD|\$)",
        normalized,
        re.IGNORECASE,
    )
    if loose:
        amount = loose.group(1).replace(",", "")
        return f"{int(amount):,} {loose.group(2).replace('$', 'USD')}"

    return None


def _parse_budget_value(budget: Optional[str]) -> float:
    if not budget:
        return 0.0
    normalized = _normalize_digits(budget).upper()
    digits = re.sub(r"[^\d.]", "", normalized.split("OMR")[0].split("USD")[0].split("ریال")[0])
    if not digits:
        return 0.0
    try:
        return float(digits)
    except ValueError:
        return 0.0


def _extract_timeline(text: str) -> Optional[str]:
    fa_match = _FA_TIMELINE_PATTERN.search(text)
    if fa_match:
        return fa_match.group(0).strip()
    en_match = _EN_TIMELINE_PATTERN.search(text)
    return en_match.group(0).strip() if en_match else None


def _extract_company(text: str) -> Optional[str]:
    for pattern in (
        r"(آژانس\s+املاک)",
        r"(کال[\s\-]*سنتر)",
        r"(شرکت\s+[\u0600-\u06FF\s]{2,40})",
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()[:80]

    fa_match = _FA_COMPANY_PATTERN.search(text)
    if fa_match:
        company = (fa_match.group(1) or fa_match.group(2) or "").strip()
        if company:
            return company[:80]

    from_match = re.search(
        r"(?:from|at)\s+([A-Za-z0-9][A-Za-z0-9\s&]{1,60}?)(?:\s*[\.،,]|$|\s+(?:budget|for|and|with)\b)",
        text,
        re.IGNORECASE,
    )
    if from_match:
        return from_match.group(1).strip()[:80]

    en_match = _EN_COMPANY_PATTERN.search(text)
    if en_match and en_match.group(1):
        return en_match.group(1).strip()[:80]

    return None


def _extract_pain_point(text: str, persian: bool) -> Optional[str]:
    lowered = text.lower()
    for keyword, en_label, fa_label in _PAIN_CATALOG:
        if keyword.lower() in lowered or keyword in text:
            return fa_label if persian else en_label
    return None


def _has_authority_signal(text: str) -> bool:
    lowered = text.lower()
    if any(signal in text for signal in _FA_AUTHORITY_SIGNALS):
        return True
    return any(signal in lowered for signal in _EN_AUTHORITY_SIGNALS)


def _honorific_name(name: Optional[str]) -> str:
    if not name:
        return "جناب"
    if _is_persian(name):
        return f"جناب {name}"
    return name


class SandboxEngine:
    """High-fidelity local emulation of gemini-1.5-flash for offline pipeline execution."""

    MODEL_ID = "gemini-1.5-flash (local-sandbox)"

    async def _simulate_latency(self, ms: int = 120) -> None:
        await asyncio.sleep(ms / 1000)

    async def generate_inbound_reply(
        self,
        user_message: str,
        history: List[Dict[str, str]],
    ) -> str:
        await self._simulate_latency(180)
        latest = _latest_user_message(history, user_message)
        text = _conversation_text(history + [{"role": "user", "content": user_message}])
        persian = _is_persian(latest) or _is_persian(text)

        budget = _extract_budget(text)
        company = _extract_company(text)
        pain = _extract_pain_point(text, persian)
        name = _extract_name(text)
        timeline = _extract_timeline(text)
        honorific = _honorific_name(name)

        if persian:
            return self._persian_inbound_reply(
                honorific=honorific,
                name=name,
                company=company,
                budget=budget,
                pain=pain,
                timeline=timeline,
            )
        return self._english_inbound_reply(
            name=name,
            company=company,
            budget=budget,
            pain=pain,
            timeline=timeline,
        )

    def _persian_inbound_reply(
        self,
        *,
        honorific: str,
        name: Optional[str],
        company: Optional[str],
        budget: Optional[str],
        pain: Optional[str],
        timeline: Optional[str],
    ) -> str:
        if name and budget and (company or pain):
            need = pain or "نیازمندی فناوری شما"
            org = company or "سازمان شما"
            return (
                f"با درود و احترام {honorific}، از ارتباط شما با آژانس فناوری رایزا سپاسگزارم. "
                f"نیازمندی {org} جهت {need} کاملاً دریافت شد. با بودجه {budget}، "
                "تیم اجرایی رایزا آماده طراحی نقشه راه اختصاصی و اجرای سریع راهکار است."
            )
        if budget and pain:
            return (
                f"{honorific}، محدوده بودجه {budget} برای این پروژه کاملاً قابل اتکاست. "
                "لطفاً بازه زمانی اجرا و سطح تصمیم‌گیری شما در تایید نهایی قرارداد را نیز اعلام بفرمایید."
            )
        if company and pain:
            return (
                f"با سپاس از پیام شما {honorific}. چالش «{pain}» در حوزه {company} "
                "دقیقاً در تخصص رایزا قرار دارد. برای تدوین پیشنهاد دقیق، بودجه مدنظر را نیز بفرمایید."
            )
        if pain:
            return (
                f"{honorific}، نیاز شما درباره «{pain}» ثبت شد. "
                "برای ارائه راهکار سازمانی، لطفاً نام مجموعه و بودجه تقریبی پروژه را نیز ارسال کنید."
            )
        return (
            "با درود و احترام، از تماس شما با آژانس فناوری رایزا سپاسگزاریم. "
            "برای ارائه مشاوره دقیق، لطفاً حوزه کسب‌وکار، چالش اصلی، بودجه و بازه زمانی اجرا را بیان بفرمایید."
        )

    def _english_inbound_reply(
        self,
        *,
        name: Optional[str],
        company: Optional[str],
        budget: Optional[str],
        pain: Optional[str],
        timeline: Optional[str],
    ) -> str:
        if name and budget and company:
            return (
                f"Excellent context, {name}. With {company}'s requirements and the {budget} budget envelope, "
                "Rayza can architect a sub-second automation pipeline tailored to your operations. "
                "I'll route your profile through our qualification matrix now."
            )
        if budget and pain:
            timeline_note = f" Your timeline of {timeline} is noted." if timeline else ""
            return (
                f"Understood. The {budget} budget range gives us strong alignment for a phased rollout.{timeline_note} "
                "Could you share who signs off on procurement?"
            )
        if company and pain:
            return (
                f"Thank you — {company}'s use case around {pain.lower()} is exactly where Rayza delivers "
                "measurable ROI. What budget range are you working with for this initiative?"
            )
        if pain:
            return (
                f"I appreciate the clarity on {pain.lower()}. Rayza specializes in high-throughput B2B "
                "automation. Which team or company should I associate with this evaluation?"
            )
        return (
            "Thank you for reaching out to Rayza Technology Agency. I'd like to understand your core "
            "software or automation challenge, the scale of your operation, and any budget or timeline "
            "constraints so I can advise you precisely."
        )

    async def extract_lead_info(self, history: List[Dict[str, str]]) -> ExtractedLeadInfo:
        await self._simulate_latency(140)
        text = _conversation_text(history)
        persian = _is_persian(text)
        return ExtractedLeadInfo(
            customer_name=_extract_name(text),
            company_name=_extract_company(text),
            budget_range=_extract_budget(text),
            primary_pain_point=_extract_pain_point(text, persian),
            timeline=_extract_timeline(text),
        )

    async def score_lead(
        self,
        data: ExtractedLeadInfo,
        conversation_text: str = "",
    ) -> LeadScoreMetadata:
        await self._simulate_latency(100)

        budget_value = _parse_budget_value(data.budget_range)
        budget_fit = 3
        if data.budget_range:
            if budget_value >= 5000 or "OMR" in (data.budget_range or "").upper():
                budget_fit = 10 if budget_value >= 5000 else 9
            elif budget_value >= 1000:
                budget_fit = 8
            else:
                budget_fit = 7

        intent_strength = 4
        if data.primary_pain_point:
            intent_strength += 3
        if data.timeline:
            intent_strength += 2
        intent_strength = min(intent_strength, 10)

        authority_level = 8 if _has_authority_signal(conversation_text) else 6
        if data.customer_name and _is_persian(conversation_text):
            authority_level = max(authority_level, 7)

        justification = (
            f"Sandbox bilingual evaluation - budget_fit={budget_fit}/10, "
            f"intent={intent_strength}/10, authority={authority_level}/10 "
            f"(parsed_budget={budget_value or 'n/a'})."
        )
        return LeadScoreMetadata(
            budget_fit=budget_fit,
            intent_strength=intent_strength,
            authority_level=authority_level,
            justification=justification,
        )

    def resolve_status(self, data: ExtractedLeadInfo, evaluation: LeadScoreMetadata) -> LeadStatus:
        avg_score = (
            evaluation.budget_fit + evaluation.intent_strength + evaluation.authority_level
        ) / 3.0
        if avg_score >= 7.0 and data.budget_range:
            return LeadStatus.QUALIFIED
        if 4.0 <= avg_score < 7.0:
            return LeadStatus.NURTURING_REQUIRED
        return LeadStatus.UNQUALIFIED
