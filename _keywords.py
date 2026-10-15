import re

_STOPWORDS = {
    "a", "an", "the", "of", "in", "to", "for", "is", "on", "and", "or",
    "with", "at", "by", "from", "up", "as", "it", "its", "be", "are",
    "was", "were", "this", "that", "these", "those", "my", "you", "your",
    "he", "she", "we", "they", "do", "did", "has", "have", "had", "not",
    "but", "so", "if", "new", "file", "copy",
}


def extract_keywords(text: str) -> list[str]:
    tokens = re.split(r"[^a-zA-Z0-9]", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]
