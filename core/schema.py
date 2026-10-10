"""
Result Schema Module

Defines the standardized result structure for all analysis tools.
All tools must return AnalysisResult instances to ensure consistent
interpretation, rendering, and export across the application.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class AnalysisResult:
    """
    Standardized result structure for all analysis tools.
    
    All detection tools must return instances of this class to ensure
    consistent interpretation and rendering. The score field is constrained
    to the range [0, 1] and represents confidence or probability.
    
    Attributes:
        label: Primary classification label (e.g., "Fake", "Fraud", "Positive")
        score: Confidence score in range [0, 1]
        model_name: Name of the model used for analysis
        model_version: Version identifier for the model
        is_demo: True if result is from a stub implementation
        details: Optional dictionary with additional analysis details
        warnings: Optional list of warning messages about the analysis
    
    Raises:
        ValueError: If score is not in the range [0, 1]
    
    Example:
        >>> result = AnalysisResult(
        ...     label="Fake",
        ...     score=0.85,
        ...     model_name="Xception Ensemble",
        ...     model_version="1.0.0",
        ...     is_demo=False,
        ...     details={"crops_analyzed": 5},
        ...     warnings=[]
        ... )
    """
    
    label: str
    score: float
    model_name: str
    model_version: str
    is_demo: bool
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """
        Validate that score is in the valid range [0, 1].
        
        Raises:
            ValueError: If score is not in range [0, 1]
        """
        if not isinstance(self.score, (int, float)):
            raise ValueError(
                f"Score must be a number, got {type(self.score).__name__}"
            )
        
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"Score must be in range [0, 1], got {self.score}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary for serialization.
        
        Returns:
            Dictionary representation suitable for JSON export
        
        Example:
            >>> result.to_dict()
            {'label': 'Fake', 'score': 0.85, ...}
        """
        return asdict(self)
    
    def to_display_dict(self) -> Dict[str, Any]:
        """
        Convert result to dictionary optimized for display in UI.
        
        Formats numeric values and adds human-readable labels.
        
        Returns:
            Dictionary with formatted values for display
        
        Example:
            >>> result.to_display_dict()
            {'Label': 'Fake', 'Confidence': '85.0%', ...}
        """
        display = {
            "Label": self.label,
            "Confidence": f"{self.score:.1%}",
            "Model": f"{self.model_name} v{self.model_version}",
            "Demo Mode": "Yes" if self.is_demo else "No",
        }
        
        # Include details if present
        if self.details:
            display.update(self.details)
        
        return display
