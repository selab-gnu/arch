"""모델 선택 — Gemini / Claude / OpenAI 중 '가지고 있는 API 키'에 맞춰 자동으로 고릅니다.

우선순위: ADK_MODEL(직접 지정) > ADK_PROVIDER(공급자 지정) > 설정된 키 자동 감지(Gemini → Claude → OpenAI)
"""

import os
import re

DEFAULT_MODELS = {
    "gemini": "gemini-3.8-flash",
    "claude": "claude-sonnet-5-5",
    "openai": "gpt-5.6",
}


def _has_key(provider: str) -> bool:
    env = os.environ
    return {
        "gemini": bool(env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY")
                       or env.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true")),
        "claude": bool(env.get("ANTHROPIC_API_KEY")),
        "openai": bool(env.get("OPENAI_API_KEY")),
    }[provider]


def _provider_of(model_name: str) -> str:
    if model_name.startswith("claude-"):
        return "claude"
    if re.match(r"(gpt-|o\d)", model_name):
        return "openai"
    return "gemini"


def resolve_model():
    """ADK에 넘길 모델을 고릅니다. 반환값: (model, 설명 문자열)

    - Gemini: 재시도 설정을 넣은 Gemini 객체로 연결합니다.
    - OpenAI: OpenAIResponsesLlm(Responses API)로 연결하며 OPENAI_API_KEY를 사용합니다.
      (문자열 'gpt-...'만 넘기면 Chat Completions 방식으로 연결되어, 추론 모델에서 도구 사용 시 400 오류)
    - Claude: 'claude-...' 문자열만 넘기면 ADK는 'Vertex AI의 Claude'로 연결해 Google Cloud 프로젝트를 요구합니다.
      Anthropic API 키(ANTHROPIC_API_KEY)로 직접 쓰려면 AnthropicLlm 객체로 감싸야 합니다.
    """
    name = os.environ.get("ADK_MODEL", "").strip()
    provider = os.environ.get("ADK_PROVIDER", "").strip().lower()
    if provider and provider not in DEFAULT_MODELS:
        raise SystemExit(f"ADK_PROVIDER는 {', '.join(DEFAULT_MODELS)} 중 하나여야 합니다 (현재: {provider}).")

    if name:
        provider = provider or _provider_of(name)
    else:
        if not provider:
            provider = next((p for p in DEFAULT_MODELS if _has_key(p)), "gemini")
        name = DEFAULT_MODELS[provider]

    vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("1", "true")
    if provider == "claude" and not vertex:
        try:
            from google.adk.models.anthropic_llm import AnthropicLlm
        except ImportError:
            raise SystemExit("Claude를 쓰려면 anthropic 패키지가 필요합니다:  pip install -U anthropic")
        return AnthropicLlm(model=name), f"Claude ({name}, Anthropic API 키)"
    if provider == "openai":
        try:
            import openai  # noqa: F401
            from google.adk.integrations.openai import OpenAIResponsesLlm
        except ImportError:
            raise SystemExit("OpenAI 모델을 쓰려면 openai 패키지가 필요합니다:  pip install -U openai")
        # Responses API(/v1/responses)로 연결합니다. gpt-5.x 같은 추론 모델은 예전 Chat Completions 방식에서
        # 도구(function tools)를 함께 쓸 수 없어 400 오류가 납니다. OPENAI_API_KEY는 SDK가 자동으로 읽습니다.
        return OpenAIResponsesLlm(model=name), f"OpenAI ({name}, OpenAI API 키)"
    if provider == "claude":
        return name, f"Claude ({name}, Vertex AI)"
    # Gemini는 일시적 오류(요청 폭주 503, 한도 429 등)에서 자동으로 재시도하도록 설정합니다.
    from google.adk.models.google_llm import Gemini
    from google.genai import types as _gtypes
    gemini = Gemini(model=name, retry_options=_gtypes.HttpRetryOptions(
        attempts=6, initial_delay=2, max_delay=30, exp_base=2,
        http_status_codes=[408, 429, 500, 502, 503, 504]))
    return gemini, f"Gemini ({name})"
