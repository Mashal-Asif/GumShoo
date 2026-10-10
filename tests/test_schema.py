"""
Unit tests for core.schema module

Tests the AnalysisResult dataclass including validation,
serialization, and display formatting.
"""

import pytest

from core.schema import AnalysisResult


def test_analysis_result_creation():
    """Test creating a valid AnalysisResult instance."""
    result = AnalysisResult(
        label="Fake",
        score=0.85,
        model_name="Xception",
        model_version="1.0.0",
        is_demo=False
    )
    
    assert result.label == "Fake"
    assert result.score == 0.85
    assert result.model_name == "Xception"
    assert result.model_version == "1.0.0"
    assert result.is_demo is False
    assert result.details == {}
    assert result.warnings == []


def test_analysis_result_with_details_and_warnings():
    """Test AnalysisResult with optional details and warnings."""
    result = AnalysisResult(
        label="Real",
        score=0.15,
        model_name="Detector",
        model_version="2.0",
        is_demo=True,
        details={"crops": 5, "spread": 0.12},
        warnings=["Demo mode active"]
    )
    
    assert result.details == {"crops": 5, "spread": 0.12}
    assert result.warnings == ["Demo mode active"]


def test_score_validation_valid_range():
    """Test that scores in valid range [0, 1] are accepted."""
    # Test boundary values
    result_zero = AnalysisResult(
        label="Test", score=0.0, model_name="M", model_version="1", is_demo=True
    )
    assert result_zero.score == 0.0
    
    result_one = AnalysisResult(
        label="Test", score=1.0, model_name="M", model_version="1", is_demo=True
    )
    assert result_one.score == 1.0
    
    # Test middle value
    result_mid = AnalysisResult(
        label="Test", score=0.5, model_name="M", model_version="1", is_demo=True
    )
    assert result_mid.score == 0.5


def test_score_validation_below_zero():
    """Test that scores below 0 raise ValueError."""
    with pytest.raises(ValueError, match="Score must be in range"):
        AnalysisResult(
            label="Test",
            score=-0.1,
            model_name="M",
            model_version="1",
            is_demo=True
        )


def test_score_validation_above_one():
    """Test that scores above 1 raise ValueError."""
    with pytest.raises(ValueError, match="Score must be in range"):
        AnalysisResult(
            label="Test",
            score=1.1,
            model_name="M",
            model_version="1",
            is_demo=True
        )


def test_score_validation_way_out_of_range():
    """Test that wildly out of range scores are rejected."""
    with pytest.raises(ValueError, match="Score must be in range"):
        AnalysisResult(
            label="Test",
            score=100.0,
            model_name="M",
            model_version="1",
            is_demo=True
        )


def test_score_validation_non_numeric():
    """Test that non-numeric scores raise ValueError."""
    with pytest.raises(ValueError, match="Score must be a number"):
        AnalysisResult(
            label="Test",
            score="high",  # type: ignore
            model_name="M",
            model_version="1",
            is_demo=True
        )


def test_to_dict_serialization():
    """Test conversion to dictionary for JSON export."""
    result = AnalysisResult(
        label="Fraud",
        score=0.92,
        model_name="FraudNet",
        model_version="3.1",
        is_demo=True,
        details={"red_flags": 3},
        warnings=["High confidence"]
    )
    
    result_dict = result.to_dict()
    
    assert isinstance(result_dict, dict)
    assert result_dict["label"] == "Fraud"
    assert result_dict["score"] == 0.92
    assert result_dict["model_name"] == "FraudNet"
    assert result_dict["model_version"] == "3.1"
    assert result_dict["is_demo"] is True
    assert result_dict["details"] == {"red_flags": 3}
    assert result_dict["warnings"] == ["High confidence"]


def test_to_display_dict_formatting():
    """Test conversion to display dictionary with formatting."""
    result = AnalysisResult(
        label="Propaganda",
        score=0.67,
        model_name="PropDetect",
        model_version="1.5.2",
        is_demo=False,
        details={"techniques": ["loaded_language", "appeal_to_fear"]}
    )
    
    display = result.to_display_dict()
    
    assert display["Label"] == "Propaganda"
    assert display["Confidence"] == "67.0%"
    assert display["Model"] == "PropDetect v1.5.2"
    assert display["Demo Mode"] == "No"
    assert display["techniques"] == ["loaded_language", "appeal_to_fear"]


def test_to_display_dict_demo_mode():
    """Test display dictionary shows Demo Mode as Yes when is_demo is True."""
    result = AnalysisResult(
        label="Test",
        score=0.5,
        model_name="Stub",
        model_version="0.0.1",
        is_demo=True
    )
    
    display = result.to_display_dict()
    assert display["Demo Mode"] == "Yes"


def test_to_display_dict_percentage_formatting():
    """Test that confidence scores are formatted as percentages."""
    result = AnalysisResult(
        label="Test",
        score=0.123,
        model_name="M",
        model_version="1",
        is_demo=True
    )
    
    display = result.to_display_dict()
    assert display["Confidence"] == "12.3%"


def test_to_display_dict_empty_details():
    """Test display dictionary when details are empty."""
    result = AnalysisResult(
        label="Test",
        score=0.5,
        model_name="M",
        model_version="1",
        is_demo=True,
        details={}
    )
    
    display = result.to_display_dict()
    
    # Should have base fields but not extra detail fields
    assert "Label" in display
    assert "Confidence" in display
    assert "Model" in display
    assert "Demo Mode" in display
    assert len(display) == 4
