"""Weather compatibility guard tests (S-08: TM59:2026 minimum = DSY1 2050s HIGH50)."""

from __future__ import annotations

from overheatlens.epw import check_tm59_2026_weather


def test_minimum_requirement_is_compatible():
    v = check_tm59_2026_weather("LEEDS_14_DSY1_2050s_HIGH50_CIBSE_v1.1.epw")
    assert v["status"] == "compatible"
    assert v["detected"] == {"dsy_type": "DSY1", "epoch": "2050s",
                             "percentile_label": "HIGH50"}


def test_more_extreme_dsy_is_research_only():
    v = check_tm59_2026_weather("LEEDS_14_DSY3_2050s_HIGH50_CIBSE_v1.1.epw")
    assert v["status"] == "research_only"
    assert "DSY3" in v["reason"]


def test_other_epoch_is_research_only():
    v = check_tm59_2026_weather("LEEDS_14_DSY1_2080s_HIGH50_CIBSE_v1.1.epw")
    assert v["status"] == "research_only"
    assert "2080s" in v["reason"]


def test_other_percentile_is_research_only():
    v = check_tm59_2026_weather("LEEDS_14_DSY1_2050s_HIGH10_CIBSE_v1.1.epw")
    assert v["status"] == "research_only"
    assert "HIGH10" in v["reason"]


def test_untraceable_filename_is_unknown():
    v = check_tm59_2026_weather("my_site_2023.epw")
    assert v["status"] == "unknown"
    assert "not machine-verifiable" in v["reason"]
