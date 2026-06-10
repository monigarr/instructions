"""Unit tests for eval metric helpers."""

from evals.metrics.field_accuracy import field_accuracy, field_accuracy_by_field
from evals.metrics.rag_precision import rag_hit_rate, rag_hit_rate_by_field


def test_field_accuracy_perfect():
    expected = [{"field": "brand_name", "status": "match"}]
    actual = [{"field": "brand_name", "status": "match"}]
    assert field_accuracy(expected, actual) == 1.0


def test_field_accuracy_partial():
    expected = [
        {"field": "brand_name", "status": "match"},
        {"field": "net_contents", "status": "mismatch"},
    ]
    actual = [
        {"field": "brand_name", "status": "match"},
        {"field": "net_contents", "status": "match"},
    ]
    assert field_accuracy(expected, actual) == 0.5


def test_field_accuracy_by_field_aggregates_rows():
    rows = [
        (
            [{"field": "brand_name", "status": "match"}],
            [{"field": "brand_name", "status": "match"}],
        ),
        (
            [
                {"field": "brand_name", "status": "needs_review"},
                {"field": "net_contents", "status": "mismatch"},
            ],
            [
                {"field": "brand_name", "status": "needs_review"},
                {"field": "net_contents", "status": "match"},
            ],
        ),
    ]
    by_field = field_accuracy_by_field(rows)
    assert by_field["brand_name"] == 1.0
    assert by_field["net_contents"] == 0.0
    assert by_field["class_type"] is None


def test_rag_hit_rate():
    assert rag_hit_rate(["a"], ["a", "b"]) == 1.0
    assert rag_hit_rate(["a"], ["b"]) == 0.0


def test_rag_hit_rate_by_field():
    rows = [
        ("government_warning", 1.0),
        ("government_warning", 0.0),
        ("brand_name", 1.0),
    ]
    by_field = rag_hit_rate_by_field(rows)
    assert by_field["government_warning"] == 0.5
    assert by_field["brand_name"] == 1.0
