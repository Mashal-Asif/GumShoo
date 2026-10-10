"""
Tool Registry Module

Provides centralized registration and discovery for analysis tools.
Tools register themselves at module import time, enabling dynamic
discovery and loose coupling between the application and tools.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Literal, Tuple


InputType = Literal["image", "text", "csv"]
ToolStatus = Literal["loaded", "fallback", "demo"]


@dataclass
class ToolMetadata:
    """
    Metadata describing a registered analysis tool.
    
    Attributes:
        name: Unique identifier for the tool (e.g., "deepfake")
        display_name: Human-readable name shown in UI
        module_number: Module number string for display (e.g., "01")
        description: Brief description of tool functionality
        accepted_input_types: List of input types the tool can process
        analyze_fn: Callable that performs the analysis
        status: Current operational status of the tool
        status_message: Optional message explaining the status
    """
    
    name: str
    display_name: str
    module_number: str
    description: str
    accepted_input_types: List[InputType]
    analyze_fn: Callable
    status: ToolStatus
    status_message: str = ""


class ToolRegistry:
    """
    Central registry for analysis tools.
    
    Provides registration, lookup, and discovery of analysis tools.
    Tools register themselves at import time, and the application
    queries the registry to discover available capabilities.
    
    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(
        ...     name="deepfake",
        ...     display_name="Deepfake Analyzer",
        ...     module_number="01",
        ...     description="Detect fake images",
        ...     accepted_input_types=["image"],
        ...     analyze_fn=analyze_image,
        ...     status="demo"
        ... )
        >>> tool = registry.get_tool("deepfake")
        >>> tool.display_name
        'Deepfake Analyzer'
    """
    
    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, ToolMetadata] = {}
    
    def register(
        self,
        name: str,
        display_name: str,
        module_number: str,
        description: str,
        accepted_input_types: List[InputType],
        analyze_fn: Callable,
        status: ToolStatus = "demo",
        status_message: str = ""
    ) -> None:
        """
        Register a tool with the registry.
        
        Tools should call this during module initialization to make
        themselves available to the application.
        
        Args:
            name: Unique identifier for the tool
            display_name: Human-readable name for display
            module_number: Module number (e.g., "01", "02")
            description: Brief description of functionality
            accepted_input_types: List of input types accepted
            analyze_fn: Function that performs analysis
            status: Current status (loaded/fallback/demo)
            status_message: Optional status explanation
        
        Raises:
            ValueError: If a tool with the same name is already registered
        
        Example:
            >>> registry.register(
            ...     name="sentiment",
            ...     display_name="Sentiment Analysis",
            ...     module_number="02",
            ...     description="Analyze text sentiment",
            ...     accepted_input_types=["text", "csv"],
            ...     analyze_fn=analyze_sentiment,
            ...     status="loaded",
            ...     status_message="Model loaded successfully"
            ... )
        """
        if name in self._tools:
            raise ValueError(
                f"Tool '{name}' is already registered. "
                f"Each tool must have a unique name."
            )
        
        # Validate input types
        valid_types: List[InputType] = ["image", "text", "csv"]
        for input_type in accepted_input_types:
            if input_type not in valid_types:
                raise ValueError(
                    f"Invalid input type '{input_type}'. "
                    f"Must be one of: {valid_types}"
                )
        
        tool = ToolMetadata(
            name=name,
            display_name=display_name,
            module_number=module_number,
            description=description,
            accepted_input_types=accepted_input_types,
            analyze_fn=analyze_fn,
            status=status,
            status_message=status_message
        )
        
        self._tools[name] = tool
    
    def get_tool(self, name: str) -> ToolMetadata:
        """
        Retrieve a tool by its unique name.
        
        Args:
            name: Unique identifier of the tool
        
        Returns:
            ToolMetadata for the requested tool
        
        Raises:
            KeyError: If no tool with the given name is registered
        
        Example:
            >>> tool = registry.get_tool("deepfake")
            >>> print(tool.display_name)
            'Deepfake Analyzer'
        """
        if name not in self._tools:
            available = ", ".join(self._tools.keys()) if self._tools else "none"
            raise KeyError(
                f"Tool '{name}' not found in registry. "
                f"Available tools: {available}"
            )
        
        return self._tools[name]
    
    def get_tools_by_input_type(self, input_type: InputType) -> List[ToolMetadata]:
        """
        Retrieve all tools that accept a specific input type.
        
        Args:
            input_type: The input type to filter by
        
        Returns:
            List of ToolMetadata for tools accepting the input type
        
        Example:
            >>> text_tools = registry.get_tools_by_input_type("text")
            >>> for tool in text_tools:
            ...     print(tool.display_name)
            'Sentiment Analysis'
            'Fraud Detection'
            'Propaganda Detection'
        """
        return [
            tool for tool in self._tools.values()
            if input_type in tool.accepted_input_types
        ]
    
    def list_all_tools(self) -> List[ToolMetadata]:
        """
        List all registered tools.
        
        Returns:
            List of all ToolMetadata in registration order
        
        Example:
            >>> all_tools = registry.list_all_tools()
            >>> len(all_tools)
            4
        """
        return list(self._tools.values())
    
    def get_tool_status(self, name: str) -> Tuple[ToolStatus, str]:
        """
        Get the current status and message for a tool.
        
        Args:
            name: Unique identifier of the tool
        
        Returns:
            Tuple of (status, status_message)
        
        Raises:
            KeyError: If no tool with the given name is registered
        
        Example:
            >>> status, message = registry.get_tool_status("deepfake")
            >>> status
            'demo'
            >>> message
            'Using stub implementation'
        """
        tool = self.get_tool(name)
        return tool.status, tool.status_message


# Global registry instance
# Tools import this and register themselves at module initialization
registry = ToolRegistry()
