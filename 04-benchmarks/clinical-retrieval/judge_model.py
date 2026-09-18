# Copyright 2026 Anacodic AI Labs — https://anacodicai.org
# SPDX-License-Identifier: Apache-2.0

"""Resolves the DeepEval "judge" LLM used to grade benchmark answers
(Faithfulness / AnswerRelevancy / ContextualPrecision / ContextualRecall).

Ported from `specialist-rag`'s `tests/benchmark/judge_model.py`, branch
`origin/fix-completion` at commit `130ff868` (not on `main`).

DeepEval metrics accept a `model=` kwarg that is either a plain OpenAI model
name (requires OPENAI_API_KEY) or a `DeepEvalBaseLLM` instance for any other
provider. This module picks whichever provider you actually have a key for,
in priority order:

    1. OPENAI_API_KEY                  -> native OpenAI judge (DeepEval default)
    2. GOOGLE_API_KEY / GEMINI_API_KEY  -> DeepEval's built-in GeminiModel
    3. GROQ_API_KEY                     -> GroqJudgeModel (below)

Override the model name for whichever provider wins with DEEPEVAL_JUDGE_MODEL.

CAUTION carried over from the copy plan: the donor's own default Groq model,
`llama-3.3-70b-versatile`, was retired by Groq on 2026-08-16 — same date as
the vision model retired in `01-modules/01-tools/01-extract/04-handwriting-ocr.ipynb`.
The MECHANISM (provider selection, the adapter classes) is what's copied;
the retired default is not. `GroqJudgeModel` below requires
`DEEPEVAL_JUDGE_MODEL` to be set explicitly rather than silently guessing
another model that might also be retired by the time this is read.
"""

from __future__ import annotations

import importlib.util
import json
import os

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_XAI_BASE_URL = "https://api.x.ai/v1"
_XAI_DEFAULT_MODEL = "grok-4.6"

try:
    # Real base class when deepeval is installed.
    from deepeval.models.base_model import DeepEvalBaseLLM
except ImportError:  # pragma: no cover - allows this module to be imported
    # (e.g. by has_judge_model() callers) even without deepeval installed.
    class DeepEvalBaseLLM:  # type: ignore[no-redef]
        def __init__(self, model_name=None):
            self.model_name = model_name


class GroqJudgeModel(DeepEvalBaseLLM):
    """DeepEval custom-model adapter for Groq.

    Groq's chat-completions API is OpenAI-SDK compatible, so this just
    points the OpenAI client at Groq's base URL. Implements both the classic
    `generate(self, prompt)` and the newer `generate(self, prompt, schema)`
    DeepEval calling convention (schema is optional either way) so it keeps
    working across DeepEval versions.
    """

    def __init__(self, model: str | None = None):
        self.model_name = model or os.getenv("DEEPEVAL_JUDGE_MODEL")
        if not self.model_name:
            raise RuntimeError(
                "GroqJudgeModel needs an explicit model -- set DEEPEVAL_JUDGE_MODEL "
                "to a currently-live Groq model id. No default is hardcoded here "
                "because the donor's own default (llama-3.3-70b-versatile) was "
                "retired by Groq on 2026-08-16."
            )
        super().__init__(self.model_name)

    def load_model(self):
        from openai import OpenAI

        return OpenAI(api_key=os.environ["GROQ_API_KEY"], base_url=_GROQ_BASE_URL)

    @staticmethod
    def _prep(prompt: str, schema) -> tuple[str, dict]:
        if schema is None:
            return prompt, {}
        return f"{prompt}\n\nRespond with valid JSON only.", {
            "response_format": {"type": "json_object"}
        }

    def generate(self, prompt: str, schema=None):
        text, kwargs = self._prep(prompt, schema)
        response = self.load_model().chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": text}],
            temperature=0,
            **kwargs,
        )
        content = response.choices[0].message.content
        return schema(**json.loads(content)) if schema is not None else content

    async def a_generate(self, prompt: str, schema=None):
        from openai import AsyncOpenAI

        text, kwargs = self._prep(prompt, schema)
        client = AsyncOpenAI(api_key=os.environ["GROQ_API_KEY"], base_url=_GROQ_BASE_URL)
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": text}],
            temperature=0,
            **kwargs,
        )
        content = response.choices[0].message.content
        return schema(**json.loads(content)) if schema is not None else content

    def get_model_name(self) -> str:
        return f"Groq/{self.model_name}"


class XAIJudgeModel(DeepEvalBaseLLM):
    """DeepEval custom-model adapter for xAI (Grok), OpenAI-compatible endpoint."""

    def __init__(self, model: str | None = None):
        self.model_name = model or os.getenv("DEEPEVAL_JUDGE_MODEL", _XAI_DEFAULT_MODEL)
        super().__init__(self.model_name)

    def load_model(self):
        from openai import OpenAI

        return OpenAI(api_key=os.environ["XAI_API_KEY"], base_url=_XAI_BASE_URL)

    @staticmethod
    def _prep(prompt: str, schema) -> tuple[str, dict]:
        if schema is None:
            return prompt, {}
        return f"{prompt}\n\nRespond with valid JSON only.", {
            "response_format": {"type": "json_object"}
        }

    def generate(self, prompt: str, schema=None):
        text, kwargs = self._prep(prompt, schema)
        response = self.load_model().chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": text}],
            temperature=0,
            **kwargs,
        )
        content = response.choices[0].message.content
        return schema(**json.loads(content)) if schema is not None else content

    async def a_generate(self, prompt: str, schema=None):
        from openai import AsyncOpenAI

        text, kwargs = self._prep(prompt, schema)
        client = AsyncOpenAI(api_key=os.environ["XAI_API_KEY"], base_url=_XAI_BASE_URL)
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": text}],
            temperature=0,
            **kwargs,
        )
        content = response.choices[0].message.content
        return schema(**json.loads(content)) if schema is not None else content

    def get_model_name(self) -> str:
        return f"xAI/{self.model_name}"


def get_judge_model():
    """Return a value suitable for a DeepEval metric's `model=` kwarg, chosen
    from whichever provider has credentials set. Returns None if none do."""
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("DEEPEVAL_JUDGE_MODEL", "gpt-4o")
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        from deepeval.models import GeminiModel

        return GeminiModel(model_name=os.getenv("DEEPEVAL_JUDGE_MODEL", "gemini-2.0-flash"))
    if os.getenv("XAI_API_KEY"):
        return XAIJudgeModel()
    if os.getenv("GROQ_API_KEY"):
        return GroqJudgeModel()
    return None


def has_judge_model() -> bool:
    return bool(
        os.getenv("OPENAI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("XAI_API_KEY")
        or os.getenv("GROQ_API_KEY")
    )


# Every provider this cookbook's notebooks check for, across stages. Kept here
# so all benchmark modules gate on the same list -- a module checking only
# OPENAI silently skips on a valid Groq-only setup.
_PIPELINE_CREDENTIAL_VARS = (
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "XAI_API_KEY",
)


def has_pipeline_credentials() -> bool:
    """True when some provider is configured to actually run a real backend."""
    return any(os.getenv(var) for var in _PIPELINE_CREDENTIAL_VARS)


def deepeval_installed() -> bool:
    """True when `import deepeval` will succeed.

    Checked separately from credentials so a missing package produces a
    clean skip rather than an error raised from inside a call site.
    """
    return importlib.util.find_spec("deepeval") is not None


def judge_shares_model_with_pipeline(pipeline_model: str, judge_model: str) -> str | None:
    """Return a warning when the judge is the same model that answered the question.

    Generalized from the donor's own version, which hardcoded a check for
    "SUPERVISOR_PROVIDER == openai and judge == gpt-4o" -- specific to a
    product concept (a supervisor agent) this cookbook doesn't have. The
    underlying question is the same regardless of what resolves either
    model: a benchmark scored by the system under test is not a benchmark.
    Pass in whatever model actually answered the question (from your
    retrieval/generation backend) and whatever `get_judge_model()` resolved
    to; returns None when there is no conflict, or when either argument is
    empty (nothing to compare).
    """
    if not pipeline_model or not judge_model:
        return None
    if pipeline_model.strip().lower() != judge_model.strip().lower():
        return None
    return (
        f"Judge model and pipeline model are both {judge_model!r}: the system "
        "under test would grade its own output. Set DEEPEVAL_JUDGE_MODEL to a "
        "different model, or run the pipeline on a different provider."
    )


__all__ = [
    "GroqJudgeModel",
    "XAIJudgeModel",
    "get_judge_model",
    "has_judge_model",
    "has_pipeline_credentials",
    "deepeval_installed",
    "judge_shares_model_with_pipeline",
]
