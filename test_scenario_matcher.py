#!/usr/bin/env python3
"""Test scenario matcher"""

from pathlib import Path
from src.onecode_skill_sanitizer.scenario_matcher import match_scenario_bundle, get_scenario_top_matches

# Test with a few tasks
test_tasks = [
    '构建一个产品官网，包含响应式设计、SEO优化和性能检查',
    '审查这个 API 的安全性，检查认证、授权和输入验证',
    '探索这个代码库的架构，找出主要模块和依赖关系',
]

bundles_path = Path('bundles/index.json')

for task in test_tasks:
    print(f'\n任务: {task}')
    print('-' * 60)

    # Get top matches
    matches = get_scenario_top_matches(task, bundles_path, top_k=3)
    for i, m in enumerate(matches, 1):
        print(f'{i}. {m["name"]} (score: {m["score"]:.3f})')

    # Get best match
    best = match_scenario_bundle(task, bundles_path)
    if best:
        print(f'\n✅ Matched: {best["name"]} (score: {best["match_score"]:.3f}, confidence: {best["match_confidence"]})')
    else:
        print('\n❌ No match above threshold')
