"""
Payment Evaluator
=================
Two-layer evaluation for the payment step of the booking flow:

  Layer 1 — Rule-based (deterministic, zero LLM cost)
  ─────────────────────────────────────────────────────
  • transaction_present  : Did the payment tool return a TXN-XXXX id?
  • card_masking_pass    : Is the full card number absent from agent output?
  • amount_match         : Does the confirmed amount match what was charged?
  • latency_ok           : Did the payment tool respond within the SLA (3 s)?

  Layer 2 — LLM-as-Judge (semantic quality)
  ─────────────────────────────────────────────────────
  • confirmation_clarity : Is the payment confirmation clear and complete?
  • failure_handling     : (only when payment failed) Was the failure explained
                           clearly with actionable next steps?
  • pci_safety           : Did the agent avoid echoing sensitive card data?

All scores (0.0 – 1.0) are posted to Langfuse on the trace identified by
``trace_id``.  Rule scores are integers (0 or 1) cast to float.
"""
from __future__ import annotations

import json
import re
import time

from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from langfuse import Langfuse

from backend.config import settings
from backend.utils.logger import logger


# ── Judge LLM ─────────────────────────────────────────────────────────────────
_judge_llm = AzureChatOpenAI(
    azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    api_key=settings.AZURE_OPENAI_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    temperature=0,
)

# ── Prompt ─────────────────────────────────────────────────────────────────────
_PAYMENT_EVAL_PROMPT = """\
You are an impartial evaluator for a hotel-booking AI assistant's payment step.

Context
-------
Payment succeeded : {payment_succeeded}
Amount charged    : {amount} {currency}
Transaction ID    : {transaction_id}

Agent output (the message shown to the user after payment):
\"\"\"{agent_response}\"\"\"

Rate each dimension on a scale of 0.0 to 1.0:

  confirmation_clarity
    Was the payment confirmation clear, complete, and professional?
    A perfect score requires: transaction ID, masked card (last 4 only),
    amount, currency, and cardholder name all present.

  failure_handling  (score 1.0 if payment succeeded — not applicable)
    If the payment failed, did the agent explain *why* and give the user
    clear, actionable next steps?  Score 0.0 if failure was ignored or
    vague, 1.0 if handled excellently.

  pci_safety
    Does the agent output avoid exposing the full card number or CVV?
    Score 1.0 if only the last 4 digits appear (or no card data at all),
    0.0 if the full card number is visible anywhere in the output.

Respond ONLY with valid JSON — no markdown, no extra text:
{{"confirmation_clarity": <float 0-1>, "failure_handling": <float 0-1>, "pci_safety": <float 0-1>, "comment": "<one-sentence justification>"}}
"""


# ── Langfuse ───────────────────────────────────────────────────────────────────
def _get_langfuse() -> Langfuse | None:
    try:
        return Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
    except Exception:
        return None


def _post_scores(trace_id: str, scores: dict[str, float], comment: str = "") -> None:
    langfuse = _get_langfuse()
    if not langfuse:
        return
    for name, value in scores.items():
        try:
            langfuse.create_score(
                trace_id=trace_id,
                name=f"payment_{name}",
                value=float(value),
                comment=comment,
            )
        except Exception as exc:
            logger.warning(f"⚠️  Langfuse score '{name}' failed: {exc}")
    langfuse.flush()
    logger.info(f"✅ Langfuse: payment evaluation scores posted to trace {trace_id}")


# ── Layer 1: Rule-based checks ─────────────────────────────────────────────────
def _rule_based_checks(
    agent_response: str,
    payment_result: dict,
    latency_s: float,
    latency_sla_s: float = 3.0,
) -> dict[str, float]:
    """
    Returns deterministic 0/1 scores for structural payment quality.

    Args:
        agent_response  : The text the booking agent showed the user.
        payment_result  : The raw dict from process_payment_service.
        latency_s       : Wall-clock seconds the payment tool took.
        latency_sla_s   : Acceptable upper bound for payment latency.
    """
    scores: dict[str, float] = {}

    # 1. transaction_present — a TXN-XXXX id must appear in the response
    txn_id: str = payment_result.get("transaction_id", "")
    scores["transaction_present"] = 1.0 if (txn_id and txn_id in agent_response) else 0.0

    # 2. card_masking_pass — full card number must NOT appear in the response
    raw_card: str = payment_result.get("_raw_card", "")
    if raw_card:
        digits = re.sub(r"[\s\-]", "", raw_card)
        # Allow last-4 to appear, but reject anything longer (≥8 consecutive digits)
        long_digit_runs = re.findall(r"\d{8,}", agent_response.replace(" ", "").replace("-", ""))
        scores["card_masking_pass"] = 0.0 if long_digit_runs else 1.0
    else:
        scores["card_masking_pass"] = 1.0  # card not available to check → assume pass

    # 3. amount_match — charged amount must appear (within rounding) in the response
    amount: float | None = payment_result.get("amount")
    currency: str = payment_result.get("currency", "")
    if amount is not None:
        amount_str = f"{amount:.2f}"
        scores["amount_match"] = 1.0 if amount_str in agent_response else 0.0
    else:
        scores["amount_match"] = 1.0  # not applicable

    # 4. latency_ok — payment must complete within the SLA
    scores["latency_ok"] = 1.0 if latency_s <= latency_sla_s else 0.0

    return scores


# ── Layer 2: LLM-as-Judge ──────────────────────────────────────────────────────
def _llm_judge(
    agent_response: str,
    payment_result: dict,
) -> dict[str, float]:
    """
    Asks the judge LLM to score confirmation_clarity, failure_handling,
    and pci_safety.  Returns {} on any failure.
    """
    succeeded: bool = payment_result.get("success", False)
    amount = payment_result.get("amount", "N/A")
    currency = payment_result.get("currency", "N/A")
    txn_id = payment_result.get("transaction_id", "N/A")

    prompt = _PAYMENT_EVAL_PROMPT.format(
        payment_succeeded=succeeded,
        amount=amount,
        currency=currency,
        transaction_id=txn_id,
        agent_response=agent_response,
    )

    try:
        result = _judge_llm.invoke([HumanMessage(content=prompt)])
        raw = result.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        return json.loads(raw)
    except Exception as exc:
        logger.warning(f"⚠️  Payment LLM-judge failed: {exc}")
        return {}


# ── Public API ─────────────────────────────────────────────────────────────────
def evaluate_payment(
    agent_response: str,
    payment_result: dict,
    latency_s: float = 0.0,
    trace_id: str | None = None,
    latency_sla_s: float = 3.0,
) -> dict:
    """
    Full two-layer payment evaluation.

    Args:
        agent_response  : The final text the booking agent displayed to the user
                          after the payment step (confirmation or error message).
        payment_result  : The raw dict returned by ``process_payment_service``.
                          Optionally include ``_raw_card`` (original card string)
                          to enable the card-masking check.
        latency_s       : How long the payment tool call took (seconds).
        trace_id        : Langfuse trace ID — scores are posted here if provided.
        latency_sla_s   : Latency threshold in seconds (default 3 s).

    Returns:
        Merged dict of all rule + LLM scores, plus a ``comment`` key from the
        LLM judge.  Empty dict on complete failure.
    """
    all_scores: dict = {}

    # ── Layer 1 ───────────────────────────────────────────────────────────────
    rule_scores = _rule_based_checks(
        agent_response=agent_response,
        payment_result=payment_result,
        latency_s=latency_s,
        latency_sla_s=latency_sla_s,
    )
    all_scores.update(rule_scores)
    logger.info(
        f"📊 Payment rule checks — "
        f"txn_present={rule_scores.get('transaction_present')}, "
        f"card_mask={rule_scores.get('card_masking_pass')}, "
        f"amount_match={rule_scores.get('amount_match')}, "
        f"latency_ok={rule_scores.get('latency_ok')} ({latency_s:.3f}s)"
    )

    # ── Layer 2 ───────────────────────────────────────────────────────────────
    llm_scores = _llm_judge(agent_response=agent_response, payment_result=payment_result)
    comment = llm_scores.pop("comment", "")
    all_scores.update(llm_scores)
    if llm_scores:
        logger.info(
            f"📊 Payment LLM-judge — "
            f"clarity={llm_scores.get('confirmation_clarity')}, "
            f"failure_handling={llm_scores.get('failure_handling')}, "
            f"pci_safety={llm_scores.get('pci_safety')} | {comment}"
        )

    # ── Post to Langfuse ──────────────────────────────────────────────────────
    if trace_id and all_scores:
        _post_scores(trace_id=trace_id, scores=all_scores, comment=comment)

    return all_scores
