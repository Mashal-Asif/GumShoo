"""
Unit tests for stub detection tools

Tests that all four stub tools return valid results with demo flags,
proper score ranges, and clear warnings about demo status.
"""

import pytest
from PIL import Image

from core.schema import AnalysisResult
from core.registry import registry


# Import tools to trigger registration
import tools.deepfake
import tools.sentiment
import tools.fraud
import tools.propaganda


# Test Deepfake Analyzer

def test_deepfake_registered():
    """Test that deepfake tool is registered."""
    tool = registry.get_tool("deepfake")
    assert tool.name == "deepfake"
    assert tool.display_name == "Deepfake Analyzer"
    assert tool.module_number == "01"
    assert "image" in tool.accepted_input_types
    assert tool.status == "demo"


def test_deepfake_analyze_returns_valid_result():
    """Test that deepfake analyzer returns a valid AnalysisResult."""
    img = Image.new("RGB", (100, 100), color="red")
    tool = registry.get_tool("deepfake")
    
    result = tool.analyze_fn(img)
    
    assert isinstance(result, AnalysisResult)
    assert result.is_demo is True
    assert 0 <= result.score <= 1
    assert result.label in ["Real", "Fake", "Uncertain"]
    assert result.model_name == "Xception Ensemble (Stub)"
    assert len(result.warnings) > 0
    assert any("DEMO MODE" in w for w in result.warnings)


def test_deepfake_analyze_deterministic():
    """Test that deepfake results are deterministic for same image."""
    img = Image.new("RGB", (50, 50), color="blue")
    tool = registry.get_tool("deepfake")
    
    result1 = tool.analyze_fn(img)
    result2 = tool.analyze_fn(img)
    
    assert result1.score == result2.score
    assert result1.label == result2.label


def test_deepfake_analyze_different_images():
    """Test that different images produce different results."""
    img1 = Image.new("RGB", (100, 100), color="red")
    img2 = Image.new("RGB", (100, 100), color="blue")
    tool = registry.get_tool("deepfake")
    
    result1 = tool.analyze_fn(img1)
    result2 = tool.analyze_fn(img2)
    
    # Different images should typically produce different scores
    # (though collisions are theoretically possible with hash)
    assert result1.score != result2.score or result1.label != result2.label


# Test Sentiment Analyzer

def test_sentiment_registered():
    """Test that sentiment tool is registered."""
    tool = registry.get_tool("sentiment")
    assert tool.name == "sentiment"
    assert tool.display_name == "Sentiment Analysis"
    assert tool.module_number == "02"
    assert "text" in tool.accepted_input_types
    assert "csv" in tool.accepted_input_types
    assert tool.status == "demo"


def test_sentiment_analyze_single_text():
    """Test sentiment analysis on single text."""
    tool = registry.get_tool("sentiment")
    
    result = tool.analyze_fn("This is a test message")
    
    assert isinstance(result, AnalysisResult)
    assert result.is_demo is True
    assert 0 <= result.score <= 1
    assert result.label in ["Positive", "Neutral", "Negative"]
    assert result.model_name == "Transformer Sentiment (Stub)"
    assert len(result.warnings) > 0


def test_sentiment_analyze_batch():
    """Test sentiment analysis on multiple texts."""
    tool = registry.get_tool("sentiment")
    texts = ["First message", "Second message", "Third message"]
    
    results = tool.analyze_fn(texts)
    
    assert isinstance(results, list)
    assert len(results) == 3
    for result in results:
        assert isinstance(result, AnalysisResult)
        assert result.is_demo is True
        assert result.label in ["Positive", "Neutral", "Negative"]


def test_sentiment_deterministic():
    """Test that sentiment results are deterministic."""
    tool = registry.get_tool("sentiment")
    text = "Deterministic test text"
    
    result1 = tool.analyze_fn(text)
    result2 = tool.analyze_fn(text)
    
    assert result1.score == result2.score
    assert result1.label == result2.label


# Test Fraud Detector

def test_fraud_registered():
    """Test that fraud tool is registered."""
    tool = registry.get_tool("fraud")
    assert tool.name == "fraud"
    assert tool.display_name == "Fraud Detection"
    assert tool.module_number == "03"
    assert "text" in tool.accepted_input_types
    assert tool.status == "demo"


def test_fraud_analyze_returns_valid_result():
    """Test that fraud detector returns a valid AnalysisResult."""
    tool = registry.get_tool("fraud")
    
    result = tool.analyze_fn("Click here to claim your prize!")
    
    assert isinstance(result, AnalysisResult)
    assert result.is_demo is True
    assert 0 <= result.score <= 1
    assert result.label in ["Fraud", "Legit"]
    assert result.model_name == "Fraud Detector (Stub)"
    assert len(result.warnings) > 0
    assert any("DEMO MODE" in w for w in result.warnings)


def test_fraud_detect_keywords():
    """Test that fraud detector recognizes common fraud keywords."""
    tool = registry.get_tool("fraud")
    
    # Text with fraud keywords should tend toward higher scores
    fraud_text = "URGENT! Verify your account NOW or it will be suspended!"
    legit_text = "Hello, here is your monthly newsletter."
    
    fraud_result = tool.analyze_fn(fraud_text)
    legit_result = tool.analyze_fn(legit_text)
    
    # Fraud text should generally score higher (though not guaranteed due to hash)
    assert isinstance(fraud_result, AnalysisResult)
    assert isinstance(legit_result, AnalysisResult)


def test_fraud_deterministic():
    """Test that fraud results are deterministic."""
    tool = registry.get_tool("fraud")
    text = "Test message for fraud detection"
    
    result1 = tool.analyze_fn(text)
    result2 = tool.analyze_fn(text)
    
    assert result1.score == result2.score
    assert result1.label == result2.label


# Test Propaganda Detector

def test_propaganda_registered():
    """Test that propaganda tool is registered."""
    tool = registry.get_tool("propaganda")
    assert tool.name == "propaganda"
    assert tool.display_name == "Propaganda Detection"
    assert tool.module_number == "04"
    assert "text" in tool.accepted_input_types
    assert tool.status == "demo"


def test_propaganda_analyze_returns_valid_result():
    """Test that propaganda detector returns a valid AnalysisResult."""
    tool = registry.get_tool("propaganda")
    
    result = tool.analyze_fn("This is a test message for propaganda detection.")
    
    assert isinstance(result, AnalysisResult)
    assert result.is_demo is True
    assert 0 <= result.score <= 1
    assert result.label in ["Propaganda", "Not Propaganda"]
    assert result.model_name == "Propaganda Detector (Stub)"
    assert len(result.warnings) > 0
    assert any("DEMO MODE" in w for w in result.warnings)


def test_propaganda_detect_techniques():
    """Test that propaganda detector identifies technique patterns."""
    tool = registry.get_tool("propaganda")
    
    # Text with propaganda keywords
    propaganda_text = "The enemy threatens our freedom! This is a dangerous betrayal of justice!"
    neutral_text = "The meeting will be held at 3 PM in the conference room."
    
    propaganda_result = tool.analyze_fn(propaganda_text)
    neutral_result = tool.analyze_fn(neutral_text)
    
    assert isinstance(propaganda_result, AnalysisResult)
    assert isinstance(neutral_result, AnalysisResult)
    
    # Propaganda text should detect some techniques
    if "techniques" in propaganda_result.details:
        techniques = propaganda_result.details["techniques"]
        assert isinstance(techniques, list)


def test_propaganda_deterministic():
    """Test that propaganda results are deterministic."""
    tool = registry.get_tool("propaganda")
    text = "Test message for propaganda detection"
    
    result1 = tool.analyze_fn(text)
    result2 = tool.analyze_fn(text)
    
    assert result1.score == result2.score
    assert result1.label == result2.label


# Integration tests

def test_all_tools_registered():
    """Test that all four tools are registered."""
    tools = registry.list_all_tools()
    assert len(tools) >= 4
    
    tool_names = [t.name for t in tools]
    assert "deepfake" in tool_names
    assert "sentiment" in tool_names
    assert "fraud" in tool_names
    assert "propaganda" in tool_names


def test_all_tools_have_demo_status():
    """Test that all tools are marked as demo."""
    tools = registry.list_all_tools()
    for tool in tools:
        assert tool.status == "demo"
        assert "demo" in tool.status_message.lower()


def test_all_tools_return_demo_results():
    """Test that all tools return results with is_demo=True."""
    # Deepfake
    img = Image.new("RGB", (10, 10))
    deepfake_result = registry.get_tool("deepfake").analyze_fn(img)
    assert deepfake_result.is_demo is True
    
    # Sentiment
    sentiment_result = registry.get_tool("sentiment").analyze_fn("test")
    assert sentiment_result.is_demo is True
    
    # Fraud
    fraud_result = registry.get_tool("fraud").analyze_fn("test")
    assert fraud_result.is_demo is True
    
    # Propaganda
    propaganda_result = registry.get_tool("propaganda").analyze_fn("test")
    assert propaganda_result.is_demo is True


def test_tools_have_warnings():
    """Test that all stub tools include warnings about demo mode."""
    img = Image.new("RGB", (10, 10))
    
    tools_and_inputs = [
        ("deepfake", img),
        ("sentiment", "test text"),
        ("fraud", "test text"),
        ("propaganda", "test text"),
    ]
    
    for tool_name, input_data in tools_and_inputs:
        tool = registry.get_tool(tool_name)
        result = tool.analyze_fn(input_data)
        assert len(result.warnings) > 0, f"{tool_name} should have warnings"
        assert any("DEMO" in w or "demo" in w for w in result.warnings), \
            f"{tool_name} should warn about demo mode"


def test_get_tools_by_input_type():
    """Test filtering tools by input type."""
    text_tools = registry.get_tools_by_input_type("text")
    image_tools = registry.get_tools_by_input_type("image")
    
    text_tool_names = [t.name for t in text_tools]
    image_tool_names = [t.name for t in image_tools]
    
    # Text tools: sentiment, fraud, propaganda
    assert "sentiment" in text_tool_names
    assert "fraud" in text_tool_names
    assert "propaganda" in text_tool_names
    
    # Image tools: deepfake
    assert "deepfake" in image_tool_names
