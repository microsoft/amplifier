"""
Output validators for microtasks (professional tone, anti-sycophancy, format checks).
"""

from __future__ import annotations

import re


class SycophancyDetector:
    SYCOPHANTIC_PATTERNS = [
        r"you['']?re absolutely right",
        r"that['']?s (a )?(brilliant|excellent|fantastic|amazing|incredible|genius)",
        r"what (a|an) (brilliant|excellent|fantastic|amazing|great) (idea|observation|insight|point)",
        r"you['']?ve (made|raised) (a|an) (excellent|great|fantastic) point",
        r"i (completely|totally|absolutely) agree",
        r"that['']?s (exactly|precisely) right",
        r"you['']?re (spot on|exactly right|absolutely correct)",
        r"your (insight|understanding|approach) is (brilliant|excellent|remarkable)",
        r"that['']?s (incredibly|remarkably) (insightful|perceptive)",
        r"i (love|admire) (that|your) (approach|thinking|idea)",
    ]

    def __init__(self) -> None:
        self.compiled = [re.compile(p, re.IGNORECASE) for p in self.SYCOPHANTIC_PATTERNS]

    def detect(self, text: str) -> tuple[bool, list[str]]:
        matches: list[str] = []
        for pat in self.compiled:
            for m in pat.findall(text):
                if isinstance(m, tuple):
                    matches.append("".join(m))
                else:
                    matches.append(m)
        return (len(matches) > 0, matches)
