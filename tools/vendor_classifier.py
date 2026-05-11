from __future__ import annotations

AI_KEYWORDS = {
    "ai", "ml", "machine learning", "artificial intelligence", "llm",
    "large language model", "generative", "gpt", "copilot", "neural",
    "predictive", "recommendation engine", "nlp", "computer vision",
}

HIGH_RISK_DATA = {"pii", "phi", "financial", "health", "biometric", "credit"}

HIGH_RISK_COUNTRIES = {
    "china", "russia", "iran", "north korea", "belarus",
}


class VendorClassifier:
    """Fast rule-based pre-classifier for vendors before AI triage."""

    def classify(
        self,
        vendor_name: str,
        data_types_shared: list[str],
        data_location: str,
        soc2_available: bool,
        uses_ai: bool,
        description: str = "",
    ) -> dict:
        data_lower = {d.lower() for d in data_types_shared}
        desc_lower = description.lower()
        country_lower = data_location.lower()

        ai_flag = uses_ai or bool(AI_KEYWORDS & set(desc_lower.split()))
        has_sensitive_data = bool(HIGH_RISK_DATA & data_lower)
        high_risk_geo = any(c in country_lower for c in HIGH_RISK_COUNTRIES)

        if has_sensitive_data and (high_risk_geo or not soc2_available):
            tier = "Critical"
        elif has_sensitive_data:
            tier = "High"
        elif ai_flag or not soc2_available:
            tier = "Medium"
        else:
            tier = "Low"

        next_steps = []
        if ai_flag:
            next_steps.append("Send AI vendor questionnaire")
        if not soc2_available:
            next_steps.append("Request SOC 2 Type II report")
        if tier in ("Critical", "High"):
            next_steps.append("Schedule vendor security review call")
        if high_risk_geo:
            next_steps.append("Escalate to legal for data transfer impact assessment")

        return {
            "risk_tier": tier,
            "ai_flag": ai_flag,
            "next_steps": next_steps,
        }
