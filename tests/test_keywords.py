import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from _keywords import extract_keywords


def test_splits_on_underscore():
    result = extract_keywords("CHM101_Syllabus_Fall2026")
    assert "syllabus" in result
    assert "chm101" in result
    assert "fall2026" in result


def test_lowercases():
    assert "myresume" in extract_keywords("MyResume")


def test_filters_stopwords():
    result = extract_keywords("the_best_of_the_year")
    assert "the" not in result
    assert "of" not in result
    assert "best" in result


def test_filters_short_tokens():
    result = extract_keywords("a_to_longer")
    assert "a" not in result
    assert "to" not in result
    assert "longer" in result


def test_empty_string_returns_empty_list():
    assert extract_keywords("") == []


def test_returns_list():
    assert isinstance(extract_keywords("hello_world"), list)
