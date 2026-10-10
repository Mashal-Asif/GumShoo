"""
Unit tests for core.registry module

Tests tool registration, retrieval, filtering, and status management.
"""

import pytest

from core.registry import ToolRegistry, ToolMetadata, InputType, ToolStatus


def dummy_analyze(*args, **kwargs):
    """Dummy analysis function for testing."""
    return None


def test_registry_initialization():
    """Test creating an empty registry."""
    registry = ToolRegistry()
    assert registry.list_all_tools() == []


def test_register_tool():
    """Test registering a single tool."""
    registry = ToolRegistry()
    
    registry.register(
        name="test_tool",
        display_name="Test Tool",
        module_number="01",
        description="A test tool",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze,
        status="demo",
        status_message="Test mode"
    )
    
    tools = registry.list_all_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"
    assert tools[0].display_name == "Test Tool"


def test_register_multiple_tools():
    """Test registering multiple tools."""
    registry = ToolRegistry()
    
    registry.register(
        name="tool1",
        display_name="Tool 1",
        module_number="01",
        description="First tool",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    registry.register(
        name="tool2",
        display_name="Tool 2",
        module_number="02",
        description="Second tool",
        accepted_input_types=["image"],
        analyze_fn=dummy_analyze
    )
    
    tools = registry.list_all_tools()
    assert len(tools) == 2
    assert tools[0].name == "tool1"
    assert tools[1].name == "tool2"


def test_register_duplicate_name_raises_error():
    """Test that registering a duplicate tool name raises ValueError."""
    registry = ToolRegistry()
    
    registry.register(
        name="duplicate",
        display_name="First",
        module_number="01",
        description="First registration",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    with pytest.raises(ValueError, match="already registered"):
        registry.register(
            name="duplicate",
            display_name="Second",
            module_number="02",
            description="Duplicate registration",
            accepted_input_types=["image"],
            analyze_fn=dummy_analyze
        )


def test_register_invalid_input_type():
    """Test that invalid input types raise ValueError."""
    registry = ToolRegistry()
    
    with pytest.raises(ValueError, match="Invalid input type"):
        registry.register(
            name="invalid",
            display_name="Invalid Tool",
            module_number="01",
            description="Has invalid input type",
            accepted_input_types=["video"],  # Invalid type
            analyze_fn=dummy_analyze
        )


def test_get_tool_by_name():
    """Test retrieving a tool by its name."""
    registry = ToolRegistry()
    
    registry.register(
        name="deepfake",
        display_name="Deepfake Analyzer",
        module_number="01",
        description="Detect fake images",
        accepted_input_types=["image"],
        analyze_fn=dummy_analyze,
        status="loaded"
    )
    
    tool = registry.get_tool("deepfake")
    
    assert tool.name == "deepfake"
    assert tool.display_name == "Deepfake Analyzer"
    assert tool.module_number == "01"
    assert tool.description == "Detect fake images"
    assert tool.accepted_input_types == ["image"]
    assert tool.analyze_fn == dummy_analyze
    assert tool.status == "loaded"


def test_get_tool_not_found():
    """Test that getting a non-existent tool raises KeyError."""
    registry = ToolRegistry()
    
    with pytest.raises(KeyError, match="not found in registry"):
        registry.get_tool("nonexistent")


def test_get_tool_not_found_shows_available():
    """Test that error message shows available tools."""
    registry = ToolRegistry()
    
    registry.register(
        name="tool1",
        display_name="Tool 1",
        module_number="01",
        description="First",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    with pytest.raises(KeyError, match="tool1"):
        registry.get_tool("nonexistent")


def test_get_tools_by_input_type_text():
    """Test filtering tools by text input type."""
    registry = ToolRegistry()
    
    registry.register(
        name="sentiment",
        display_name="Sentiment",
        module_number="02",
        description="Text analysis",
        accepted_input_types=["text", "csv"],
        analyze_fn=dummy_analyze
    )
    
    registry.register(
        name="deepfake",
        display_name="Deepfake",
        module_number="01",
        description="Image analysis",
        accepted_input_types=["image"],
        analyze_fn=dummy_analyze
    )
    
    registry.register(
        name="fraud",
        display_name="Fraud",
        module_number="03",
        description="Text fraud",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    text_tools = registry.get_tools_by_input_type("text")
    
    assert len(text_tools) == 2
    assert text_tools[0].name == "sentiment"
    assert text_tools[1].name == "fraud"


def test_get_tools_by_input_type_image():
    """Test filtering tools by image input type."""
    registry = ToolRegistry()
    
    registry.register(
        name="deepfake",
        display_name="Deepfake",
        module_number="01",
        description="Image analysis",
        accepted_input_types=["image"],
        analyze_fn=dummy_analyze
    )
    
    registry.register(
        name="sentiment",
        display_name="Sentiment",
        module_number="02",
        description="Text analysis",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    image_tools = registry.get_tools_by_input_type("image")
    
    assert len(image_tools) == 1
    assert image_tools[0].name == "deepfake"


def test_get_tools_by_input_type_no_matches():
    """Test filtering with input type that has no matching tools."""
    registry = ToolRegistry()
    
    registry.register(
        name="sentiment",
        display_name="Sentiment",
        module_number="02",
        description="Text only",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    image_tools = registry.get_tools_by_input_type("image")
    assert image_tools == []


def test_list_all_tools():
    """Test listing all registered tools."""
    registry = ToolRegistry()
    
    registry.register(
        name="tool1",
        display_name="Tool 1",
        module_number="01",
        description="First",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze
    )
    
    registry.register(
        name="tool2",
        display_name="Tool 2",
        module_number="02",
        description="Second",
        accepted_input_types=["image"],
        analyze_fn=dummy_analyze
    )
    
    registry.register(
        name="tool3",
        display_name="Tool 3",
        module_number="03",
        description="Third",
        accepted_input_types=["csv"],
        analyze_fn=dummy_analyze
    )
    
    all_tools = registry.list_all_tools()
    
    assert len(all_tools) == 3
    assert all_tools[0].name == "tool1"
    assert all_tools[1].name == "tool2"
    assert all_tools[2].name == "tool3"


def test_get_tool_status():
    """Test retrieving tool status and message."""
    registry = ToolRegistry()
    
    registry.register(
        name="test_tool",
        display_name="Test",
        module_number="01",
        description="Test tool",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze,
        status="fallback",
        status_message="Model not found, using fallback"
    )
    
    status, message = registry.get_tool_status("test_tool")
    
    assert status == "fallback"
    assert message == "Model not found, using fallback"


def test_get_tool_status_default_message():
    """Test tool status with default empty message."""
    registry = ToolRegistry()
    
    registry.register(
        name="test_tool",
        display_name="Test",
        module_number="01",
        description="Test tool",
        accepted_input_types=["text"],
        analyze_fn=dummy_analyze,
        status="loaded"
    )
    
    status, message = registry.get_tool_status("test_tool")
    
    assert status == "loaded"
    assert message == ""


def test_tool_with_multiple_input_types():
    """Test tool that accepts multiple input types."""
    registry = ToolRegistry()
    
    registry.register(
        name="multi_tool",
        display_name="Multi Tool",
        module_number="01",
        description="Accepts multiple types",
        accepted_input_types=["text", "csv", "image"],
        analyze_fn=dummy_analyze
    )
    
    tool = registry.get_tool("multi_tool")
    assert len(tool.accepted_input_types) == 3
    assert "text" in tool.accepted_input_types
    assert "csv" in tool.accepted_input_types
    assert "image" in tool.accepted_input_types
    
    # Tool should appear in filters for all its input types
    text_tools = registry.get_tools_by_input_type("text")
    csv_tools = registry.get_tools_by_input_type("csv")
    image_tools = registry.get_tools_by_input_type("image")
    
    assert tool in text_tools
    assert tool in csv_tools
    assert tool in image_tools
