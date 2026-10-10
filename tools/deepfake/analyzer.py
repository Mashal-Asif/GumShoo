"""
Deepfake Detection Analyzer

Real AI-based deepfake detection using Xception ensemble models.
Uses two trained Xception models for robust image authenticity analysis.
"""

import sys
from pathlib import Path
from PIL import Image

from core.schema import AnalysisResult

# Add deepfake model directory to path
DEEPFAKE_MODEL_DIR = Path(__file__).parent.parent.parent / "deepfake_model"
sys.path.insert(0, str(DEEPFAKE_MODEL_DIR))

try:
    from detector import DeepfakeDetector
    _detector = DeepfakeDetector()
    _model_available = True
    _model_error = None
except Exception as e:
    _detector = None
    _model_available = False
    _model_error = str(e)


def analyze_image(image: Image.Image) -> AnalysisResult:
    """
    Analyze image for deepfake/manipulation using trained Xception ensemble.
    
    Uses an ensemble of two Xception models trained on deepfake datasets.
    Analyzes multiple crops of the image and provides uncertainty estimates
    based on model agreement and prediction spread.
    
    Args:
        image: PIL Image to analyze for authenticity
    
    Returns:
        AnalysisResult with real AI-based deepfake analysis
    
    Example:
        >>> result = analyze_image(pil_image)
        >>> result.is_demo
        False
        >>> result.label in ["Real", "Fake", "Uncertain"]
        True
    """
    if not _model_available:
        return AnalysisResult(
            label="Error",
            score=0.0,
            model_name="Xception Ensemble",
            model_version="2.0.0",
            is_demo=False,
            details={
                "error": f"Model not available: {_model_error}",
                "image_size": f"{image.size[0]}x{image.size[1]}",
                "image_mode": image.mode
            },
            warnings=[
                f"Model loading failed: {_model_error}",
                "Cannot perform deepfake analysis without trained models"
            ]
        )
    
    try:
        # Get prediction from the ensemble detector
        result = _detector.predict(image)
        
        verdict = result["verdict"]
        p_real = result["p_real"]
        p_fake = result["p_fake"]
        
        # Map verdict to our label system
        if verdict == "REAL":
            label = "Real"
            score = p_real
        elif verdict == "FAKE":
            label = "Fake"
            score = p_fake
        else:  # UNCERTAIN
            label = "Uncertain"
            score = 0.5  # Neutral score for uncertain cases
        
        # Determine confidence level
        if verdict == "UNCERTAIN":
            confidence_desc = "Uncertain"
        elif max(p_real, p_fake) >= 0.8:
            confidence_desc = "High"
        elif max(p_real, p_fake) >= 0.6:
            confidence_desc = "Medium" 
        else:
            confidence_desc = "Low"
        
        # Build warning messages
        warnings = []
        if result["spread"] > 0.15:
            warnings.append("High prediction spread across image crops - results may be inconsistent")
        if result["model_gap"] > 0.3:
            warnings.append("Models disagree significantly - interpretation should be cautious")
        if verdict == "UNCERTAIN":
            warnings.append("Prediction is uncertain - manual verification recommended")
        
        return AnalysisResult(
            label=label,
            score=score,
            model_name="Xception Ensemble",
            model_version="2.0.0", 
            is_demo=False,
            details={
                "verdict": f"{verdict} ({confidence_desc} confidence)",
                "p_real": f"{p_real:.3f}",
                "p_fake": f"{p_fake:.3f}",
                "image_size": f"{image.size[0]}x{image.size[1]}",
                "crops_analyzed": result["crops"],
                "prediction_spread": f"{result['spread']:.3f}",
                "model_agreement": f"Gap: {result['model_gap']:.3f}",
                "per_model_results": result["per_model"],
                "analysis": f"Ensemble analysis of {result['crops']} image crops using dual Xception networks",
                "model_architecture": "Xception CNN trained on deepfake datasets"
            },
            warnings=warnings
        )
        
    except Exception as e:
        return AnalysisResult(
            label="Error",
            score=0.0,
            model_name="Xception Ensemble",
            model_version="2.0.0",
            is_demo=False,
            details={
                "error": f"Analysis failed: {str(e)}",
                "image_size": f"{image.size[0]}x{image.size[1]}",
                "image_mode": image.mode
            },
            warnings=[
                f"Analysis error: {str(e)}",
                "Could not complete deepfake detection"
            ]
        )
