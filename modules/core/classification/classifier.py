import logging
import re
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from core.classification.config import config
from core.classification.prompts import SYSTEM_PROMPT
from core.classification.registry import DOCUMENT_TYPE_RULES
from core.classification.schemas import ClassificationResult

logger = logging.getLogger(__name__)


class DocumentClassifier:
    _CLEAN_TAGS = re.compile(r"<[^>]+>")
    _CLEAN_MARKDOWN = re.compile(r"[*_`#>-]")
    _CLEAN_WHITESPACE = re.compile(r"\s+")

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or config.api_key

        self.client = genai.Client(api_key=key) if key else None

        if not self.client:
            logger.warning(
                "Gemini API key is missing. "
                "LLM classification fallback will be disabled."
            )
        else:
            logger.debug("Gemini client initialized for classification.")

    def classify(self, markdown: str) -> ClassificationResult:
        if not markdown or not markdown.strip():
            return ClassificationResult(
                domain="unknown",
                document_type="unknown",
                confidence=0.0,
                method="fallback",
                reason="Document contains no readable content.",
            )

        clean_text = self._normalize_text(markdown)
        tokens = clean_text.split()
        header_text = " ".join(tokens[:config.header_word_limit])

        scores, matched = self._calculate_scores(header_text, clean_text)

        # specialized_type = self._resolve_specialized_type(scores, clean_text)

        # if specialized_type:
        #     rule = DOCUMENT_TYPE_RULES[specialized_type]
        #     return ClassificationResult(
        #         domain=rule.domain,
        #         document_type=specialized_type,
        #         confidence=0.95,
        #         method="rules",
        #         reason=(
        #             f"Matched specialized document type: "
        #             f"{specialized_type}"
        #         ),
        #     )

        best_rule_result = None

        if scores:
            ranked = sorted(
                scores.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            best_type, best_score = ranked[0]
            second_score = ranked[1][1] if len(ranked) > 1 else 0.0

            confidence = self._calculate_confidence(
                best_score,
                second_score,
            )

            rule = DOCUMENT_TYPE_RULES[best_type]

            best_rule_result = ClassificationResult(
                domain=rule.domain,
                document_type=best_type,
                confidence=confidence,
                method="rules",
                reason=(
                    f"Matched keywords: "
                    f"{', '.join(matched[best_type][:3])}"
                ),
            )

            if confidence >= config.high_confidence_threshold:
                return best_rule_result

        if self.client:
            return self._classify_with_llm(header_text)

        if best_rule_result:
            return best_rule_result.model_copy(
                update={
                    "method": "fallback",
                    "reason": (
                        f"{best_rule_result.reason}. "
                        "LLM fallback was unavailable."
                    ),
                }
            )

        return ClassificationResult(
            domain="unknown",
            document_type="unknown",
            confidence=0.0,
            method="fallback",
            reason="No classification rule matched and LLM was unavailable.",
        )

    @classmethod
    def _normalize_text(cls, markdown: str) -> str:
        text = markdown.lower()
        text = cls._CLEAN_TAGS.sub(" ", text)
        text = cls._CLEAN_MARKDOWN.sub(" ", text)
        return cls._CLEAN_WHITESPACE.sub(" ", text).strip()

    @staticmethod
    def _resolve_specialized_type(
        scores: dict[str, float],
        text: str,
    ) -> str | None:
        specialized_types = (
            "department_circular",
            "faculty_notice",
            "faculty_workload",
            "faculty_timetable",
            "faculty_meeting_notice",
            "meeting_agenda",
            "meeting_minutes",
            "department_activity_report",
            "faculty_development_program",
            "workshop",
            "seminar",
            "conference",
        )

        matched_specialized = [
            doc_type
            for doc_type in specialized_types
            if doc_type in scores
        ]

        if not matched_specialized:
            return None

        # Select the specialized type with the highest score.
        return max(
            matched_specialized,
            key=lambda doc_type: scores[doc_type],
        )

    @staticmethod
    def _calculate_scores(header: str, body: str) -> tuple[dict[str, float], dict[str, list[str]]]:
        scores = {}
        matched_keywords = {}

        for doc_type, rule in DOCUMENT_TYPE_RULES.items():
            score = 0.0
            matches = []

            # 1. Standard Keywords (Header = 3.0, Body = 1.0)
            for idx, pattern in enumerate(rule.compiled_keywords):
                kw_str = rule.keywords[idx]
                if pattern.search(header):
                    score += 3.0
                    matches.append(kw_str)
                elif pattern.search(body):
                    score += 1.0
                    matches.append(kw_str)

            # 2. Strong Keywords (Header = 8.0, Body = 3.0)
            for idx, pattern in enumerate(rule.compiled_strong_keywords):
                skw_str = rule.strong_keywords[idx]
                if pattern.search(header):
                    score += 8.0
                    matches.append(skw_str)
                elif pattern.search(body):
                    score += 3.0
                    matches.append(skw_str)

            if score > 0:
                scores[doc_type] = score
                matched_keywords[doc_type] = matches

        return scores, matched_keywords

    @staticmethod
    def _calculate_confidence(best_score: float, second_score: float) -> float:
        margin = best_score - second_score
        
        if best_score >= 10.0 and margin >= 6.0:
            return 0.95
        if best_score >= 6.0 and margin >= 3.0:
            return 0.85
        if best_score >= 3.0 and margin >= 1.5:
            return 0.70
        return 0.50

    def _classify_with_llm(self, excerpt: str) -> ClassificationResult:
        try:
            response = self.client.models.generate_content(
                model=config.llm_model_name,
                contents=f"Document snippet:\n{excerpt}",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0,
                    response_mime_type="application/json",
                    response_schema=ClassificationResult,
                ),
            )
            result = ClassificationResult.model_validate_json(response.text)
            return result.model_copy(update={"method": "llm"})
        except Exception as exc:
            logger.error("LLM classification failed: %s", exc)
            return ClassificationResult(
                domain="unknown",
                document_type="unknown",
                confidence=0.0,
                method="fallback",
                reason=f"LLM extraction error: {exc}",
            )


def classify_file(file_path: str | Path, api_key: Optional[str] = None) -> ClassificationResult:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    markdown = path.read_text(encoding="utf-8")
    classifier = DocumentClassifier(api_key=api_key)
    return classifier.classify(markdown)