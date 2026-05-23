from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from domain.cockpit import build_ai_reasoning_context, build_template_reasoning


LLMMode = Literal["disabled", "local", "api"]


class LLMClient(Protocol):
    def generate_reasoning(self, context: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class LLMAdapterService:
    mode: LLMMode = "disabled"
    local_client: LLMClient | None = None
    api_client: LLMClient | None = None

    def explain(self, cockpit_result: object) -> dict[str, Any]:
        context = build_ai_reasoning_context(cockpit_result)
        if self.mode == "disabled":
            return build_template_reasoning(context)

        if self.mode == "local":
            if self.local_client is None:
                return _not_available(
                    "Local LLM mode requested but no local client is configured.",
                    mode="local",
                )
            return self._safe_generate(self.local_client, context, mode="local")

        if self.mode == "api":
            if self.api_client is None:
                return _not_available(
                    "API LLM mode requested but no API client is configured.",
                    mode="api",
                )
            return self._safe_generate(self.api_client, context, mode="api")

        return _not_available(f"Unsupported LLM mode: {self.mode}", mode=str(self.mode))

    def _safe_generate(self, client: LLMClient, context: dict[str, Any], mode: LLMMode) -> dict[str, Any]:
        try:
            payload = client.generate_reasoning(context)
        except Exception as exc:
            return _not_available(f"{mode} LLM client failed: {exc}", mode=mode)
        if not isinstance(payload, dict):
            return _not_available(f"{mode} LLM client returned invalid payload.", mode=mode)
        return {
            "status": str(payload.get("status", "available")),
            "mode": mode,
            "summary": str(payload.get("summary", "")),
            "reasoning_points": payload.get("reasoning_points", []),
            "caveats": payload.get("caveats", []),
        }


def _not_available(reason: str, mode: str = "disabled") -> dict[str, Any]:
    return {
        "status": "not_available",
        "mode": mode,
        "summary": "AI reasoning is not available.",
        "reasoning_points": [],
        "caveats": [
            reason,
            "No LLM provider is required for default local/dev mode.",
        ],
    }
