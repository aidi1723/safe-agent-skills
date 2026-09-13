"""
Scenario Bundle Matcher for Router v3

Matches tasks to scenario bundles using keyword overlap,
example similarity, and description matching.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# Scenario matching threshold
SCENARIO_MATCH_THRESHOLD = 0.15


def load_scenario_bundles(bundles_path: Path) -> list[dict[str, Any]]:
    """Load all scenario bundles from index.json"""
    if not bundles_path.exists():
        return []

    content = bundles_path.read_text(encoding="utf-8")
    data = json.loads(content)
    return data.get("bundles", [])


def normalize_text(text: str) -> str:
    """Normalize text for matching: lowercase, remove punctuation"""
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation but keep spaces and Chinese characters
    text = re.sub(r'[^\w\s一-鿿]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_tokens(text: str) -> set[str]:
    """Extract word tokens from text, handling both English and Chinese"""
    normalized = normalize_text(text)

    tokens = set()

    # Split on whitespace to get initial tokens
    words = normalized.split()

    for word in words:
        # For primarily Chinese text (more than 50% Chinese chars)
        chinese_chars = len([c for c in word if '一' <= c <= '鿿'])
        if chinese_chars > len(word) * 0.5:
            # Extract individual Chinese characters and bigrams
            for i, char in enumerate(word):
                if '一' <= char <= '鿿':
                    tokens.add(char)
                    # Add bigrams
                    if i < len(word) - 1:
                        next_char = word[i + 1]
                        if '一' <= next_char <= '鿿':
                            tokens.add(char + next_char)
        else:
            # English or mixed: keep as whole word if >= 2 chars
            if len(word) >= 2:
                tokens.add(word)

    return tokens


def keyword_overlap_score(task: str, keywords: list[str]) -> float:
    """
    Calculate keyword overlap score

    Returns: 0.0 to 1.0
    """
    if not keywords:
        return 0.0

    task_tokens = extract_tokens(task)
    keyword_tokens = set()
    for kw in keywords:
        keyword_tokens.update(extract_tokens(kw))

    if not keyword_tokens:
        return 0.0

    # Calculate Jaccard similarity
    intersection = task_tokens & keyword_tokens
    union = task_tokens | keyword_tokens

    if not union:
        return 0.0

    return len(intersection) / len(union)


def description_similarity_score(task: str, description: str) -> float:
    """
    Calculate description similarity score

    Returns: 0.0 to 1.0
    """
    if not description:
        return 0.0

    task_tokens = extract_tokens(task)
    desc_tokens = extract_tokens(description)

    if not desc_tokens:
        return 0.0

    # Calculate Jaccard similarity
    intersection = task_tokens & desc_tokens
    union = task_tokens | desc_tokens

    if not union:
        return 0.0

    return len(intersection) / len(union)


def task_signals_match_score(task: str, signals: list[str]) -> float:
    """
    Calculate task signals match score

    Task signals are strong indicators that a task belongs to this scenario.
    Higher weight than general keywords.

    Returns: 0.0 to 1.0
    """
    if not signals:
        return 0.0

    task_lower = task.lower()
    task_tokens = extract_tokens(task)
    matched_weight = 0.0
    total_weight = 0.0

    for signal in signals:
        signal_lower = signal.lower()
        signal_tokens = extract_tokens(signal)

        # Base weight
        weight = 1.0
        total_weight += weight

        # 1. Exact substring match (full credit)
        if signal_lower in task_lower:
            matched_weight += weight
            continue

        # 2. Token overlap match
        if signal_tokens:
            overlap = len(signal_tokens & task_tokens)
            if overlap > 0:
                # Give credit proportional to how much of the signal matched
                overlap_ratio = overlap / len(signal_tokens)
                # Boost longer overlaps
                if overlap >= 2:
                    overlap_ratio = min(1.0, overlap_ratio * 1.5)
                matched_weight += weight * overlap_ratio

    # Return weighted proportion
    return matched_weight / total_weight if total_weight > 0 else 0.0


def calculate_scenario_score(
    task: str,
    scenario: dict[str, Any]
) -> float:
    """
    Calculate overall matching score between task and scenario

    Scoring components:
    - task_signals (60%): Strong indicators from bundle definition
    - description (25%): Similarity to scenario description
    - keywords (15%): General keyword overlap

    Returns: 0.0 to 1.0
    """
    # Extract scenario metadata
    description = scenario.get("scenario", "")
    task_signals = scenario.get("task_signals", [])

    # Calculate component scores
    signals_score = task_signals_match_score(task, task_signals)
    desc_score = description_similarity_score(task, description)

    # Keywords derived from task_signals + scenario name
    keywords = task_signals + [scenario.get("name", "")]
    keyword_score = keyword_overlap_score(task, keywords)

    # Weighted combination - prioritize task_signals more heavily
    total_score = (
        signals_score * 0.60 +
        desc_score * 0.25 +
        keyword_score * 0.15
    )

    return total_score


def match_scenario_bundle(
    task: str,
    bundles_path: Path,
    threshold: float = SCENARIO_MATCH_THRESHOLD
) -> dict[str, Any] | None:
    """
    Match task to best scenario bundle

    Args:
        task: Normalized task description
        bundles_path: Path to bundles/index.json
        threshold: Minimum score to accept a match (default 0.30)

    Returns:
        Matched scenario dict with added 'match_score', or None
    """
    bundles = load_scenario_bundles(bundles_path)

    if not bundles:
        return None

    # Score all bundles
    scored_bundles = []
    for bundle in bundles:
        score = calculate_scenario_score(task, bundle)
        scored_bundles.append((bundle, score))

    # Sort by score descending
    scored_bundles.sort(key=lambda x: x[1], reverse=True)

    # Return best match if above threshold
    best_bundle, best_score = scored_bundles[0]

    if best_score >= threshold:
        # Return bundle with match score attached
        return {
            **best_bundle,
            "match_score": best_score,
            "match_confidence": "high" if best_score >= 0.6 else "medium"
        }

    return None


def get_scenario_top_matches(
    task: str,
    bundles_path: Path,
    top_k: int = 3
) -> list[dict[str, Any]]:
    """
    Get top-k scenario matches with scores (for debugging)

    Returns:
        List of (scenario, score) tuples, sorted by score
    """
    bundles = load_scenario_bundles(bundles_path)

    if not bundles:
        return []

    scored = []
    for bundle in bundles:
        score = calculate_scenario_score(task, bundle)
        scored.append({
            "id": bundle.get("id"),
            "name": bundle.get("name"),
            "score": score,
            "scenario": bundle.get("scenario", ""),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def apply_bundle_selection_logic(
    bundle: dict[str, Any],
    task: str
) -> list[str]:
    """
    Apply core/conditional selection logic to bundle.
    
    For Bundle v2 schema with core_skills and conditional_skills.
    Falls back to legacy 'skills' field if core_skills is absent.
    
    Args:
        bundle: Matched scenario bundle
        task: Original task description
    
    Returns:
        List of skill names to select for this task
    """
    # Bundle v2: Use core_skills + conditional matching
    if "core_skills" in bundle:
        selected = list(bundle.get("core_skills", []))
        
        # Check each conditional skill trigger
        for conditional in bundle.get("conditional_skills", []):
            trigger = conditional.get("trigger", "")
            if trigger and re.search(trigger, task, re.IGNORECASE):
                selected.extend(conditional.get("skills", []))
        
        return selected
    
    # Bundle v1: Use legacy skills field
    return list(bundle.get("skills", []))


def match_scenario_bundle_v2(
    task: str,
    bundles_path: Path,
    threshold: float = SCENARIO_MATCH_THRESHOLD
) -> dict[str, Any] | None:
    """
    Match task to best scenario bundle using Bundle v2 schema (core + conditional).
    
    Args:
        task: Normalized task description
        bundles_path: Path to bundles/index-v2-tier1.json or bundles/index.json
        threshold: Minimum score to accept a match (default 0.30)
    
    Returns:
        Matched scenario dict with skills selected via core/conditional logic, or None
    """
    bundles = load_scenario_bundles(bundles_path)
    
    if not bundles:
        return None
    
    # Score all bundles
    scored_bundles = []
    for bundle in bundles:
        score = calculate_scenario_score(task, bundle)
        scored_bundles.append((bundle, score))
    
    # Sort by score descending
    scored_bundles.sort(key=lambda x: x[1], reverse=True)
    
    # Return best match if above threshold
    best_bundle, best_score = scored_bundles[0]
    
    if best_score >= threshold:
        # Apply core + conditional selection logic
        selected_skills = apply_bundle_selection_logic(best_bundle, task)
        
        # Count core and conditional skills
        core_count = len(best_bundle.get("core_skills", []))
        conditional_matched = []
        conditional_skipped = []
        
        for conditional in best_bundle.get("conditional_skills", []):
            trigger = conditional.get("trigger", "")
            if trigger and re.search(trigger, task, re.IGNORECASE):
                conditional_matched.append({
                    "trigger": trigger,
                    "skills": conditional.get("skills", [])
                })
            else:
                conditional_skipped.append({
                    "trigger": trigger,
                    "skills": conditional.get("skills", [])
                })
        
        return {
            **best_bundle,
            "skills": selected_skills,
            "match_score": best_score,
            "match_confidence": "high" if best_score >= 0.6 else "medium",
            "skill_selection": {
                "core_count": core_count,
                "conditional_matched": conditional_matched,
                "conditional_skipped": conditional_skipped,
                "total_selected": len(selected_skills)
            }
        }
    
    return None
