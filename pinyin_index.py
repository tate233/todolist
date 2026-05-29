"""Lightweight pinyin + fuzzy matching (no heavy dependencies).

A small built-in CJK->pinyin map covers common characters; unknown characters
fall back to themselves. This powers pinyin / pinyin-initial recall and a
bounded edit-distance fuzzy fallback for typo tolerance.
"""
from typing import List

# Compact map of common Chinese characters to pinyin (extend as needed).
_PINYIN = {
    "北": "bei", "京": "jing", "上": "shang", "海": "hai", "广": "guang",
    "州": "zhou", "深": "shen", "圳": "zhen", "中": "zhong", "国": "guo",
    "学": "xue", "习": "xi", "笔": "bi", "记": "ji", "工": "gong",
    "作": "zuo", "生": "sheng", "活": "huo", "项": "xiang", "目": "mu",
    "想": "xiang", "法": "fa", "今": "jin", "天": "tian", "明": "ming",
    "编": "bian", "程": "cheng", "教": "jiao", "搜": "sou", "索": "suo",
    "任": "ren", "务": "wu", "文": "wen", "件": "jian", "数": "shu",
    "据": "ju", "时": "shi", "间": "jian", "标": "biao", "题": "ti",
}


def to_pinyin(text: str) -> str:
    """Full pinyin of text (known chars mapped, others kept)."""
    out = [_PINYIN.get(ch, ch if ch.isascii() else "") for ch in text]
    return "".join(out).lower()


def to_initials(text: str) -> str:
    """First letters of each character's pinyin (e.g. 北京 -> bj)."""
    out = []
    for ch in text:
        py = _PINYIN.get(ch)
        if py:
            out.append(py[0])
        elif ch.isascii() and ch.isalnum():
            out.append(ch.lower())
    return "".join(out)


def matches_pinyin(query: str, text: str) -> bool:
    """True if query matches text's full pinyin or pinyin initials."""
    q = query.lower()
    return bool(q) and (q in to_pinyin(text) or q in to_initials(text))


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance (iterative DP)."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fuzzy_match(query: str, term: str, max_distance: int = 1) -> bool:
    """True if query is within max_distance edits of term (or a prefix region)."""
    if not query:
        return False
    if query in term:
        return True
    return edit_distance(query, term) <= max_distance


def suggest(prefix: str, terms: List[str], limit: int = 5) -> List[str]:
    """Prefix suggestions across literal terms and their pinyin/initials."""
    p = prefix.lower()
    hits = [t for t in terms
            if t.lower().startswith(p) or to_pinyin(t).startswith(p) or to_initials(t).startswith(p)]
    return hits[:limit]
