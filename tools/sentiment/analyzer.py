"""
Sentiment Analysis Analyzer

Real sentiment analysis using VADER (Valence Aware Dictionary and sEntiment Reasoner).
VADER is specifically tuned for social media text and provides robust sentiment classification.
"""

from typing import List, Union

from core.schema import AnalysisResult

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _analyzer = SentimentIntensityAnalyzer()
    _model_available = True
    _model_error = None
except ImportError as e:
    _analyzer = None
    _model_available = False
    _model_error = str(e)


def analyze_text(texts: Union[str, List[str]]) -> Union[AnalysisResult, List[AnalysisResult]]:
    """
    Analyze text for sentiment using VADER sentiment analysis.
    
    VADER provides lexicon and rule-based sentiment analysis that is 
    specifically attuned to social media text, and works well on 
    social media content, NY Times editorials, movie reviews, and more.
    
    Args:
        texts: Single text string or list of text strings
    
    Returns:
        Single AnalysisResult or list of AnalysisResults (matching input type)
    
    Example:
        >>> result = analyze_text("I love this product!")
        >>> result.is_demo
        False
        >>> result.label in ["Positive", "Neutral", "Negative"]
        True
        
        >>> results = analyze_text(["Great!", "Terrible!"])
        >>> len(results)
        2
    """
    if not _model_available:
        # Return error result if VADER not available
        error_result = AnalysisResult(
            label="Error",
            score=0.0,
            model_name="VADER Sentiment",
            model_version="3.3.2",
            is_demo=False,
            details={
                "error": f"VADER not available: {_model_error}",
                "text_length": len(texts) if isinstance(texts, str) else len(str(texts))
            },
            warnings=[
                f"Model loading failed: {_model_error}",
                "Cannot perform sentiment analysis without VADER"
            ]
        )
        return error_result if isinstance(texts, str) else [error_result] * len(texts)
    
    # Handle single text
    if isinstance(texts, str):
        return _analyze_single_text(texts)
    
    # Handle batch processing
    return [_analyze_single_text(text) for text in texts]


def _analyze_single_text(text: str) -> AnalysisResult:
    """Analyze a single text for sentiment using VADER."""
    if not _model_available:
        return AnalysisResult(
            label="Error",
            score=0.0,
            model_name="VADER Sentiment",
            model_version="3.3.2",
            is_demo=False,
            details={"error": f"VADER not available: {_model_error}"},
            warnings=[f"Model loading failed: {_model_error}"]
        )
    
    try:
        # Get VADER sentiment scores
        scores = _analyzer.polarity_scores(text)
        
        # Extract individual components
        negative = scores['neg']
        neutral = scores['neu'] 
        positive = scores['pos']
        compound = scores['compound']
        
        # Determine label and score based on compound score
        # VADER compound score ranges from -1 (most extreme negative) to +1 (most extreme positive)
        if compound >= 0.05:
            label = "Positive"
            score = (compound + 1) / 2  # Convert -1,1 to 0,1 range
            description = "Text expresses positive sentiment"
        elif compound <= -0.05:
            label = "Negative"  
            score = abs(compound)  # Use absolute value for negative sentiment strength
            description = "Text expresses negative sentiment"
        else:
            label = "Neutral"
            score = 0.5  # Neutral baseline
            description = "Text is neutral or mixed sentiment"
        
        # Determine confidence based on how extreme the compound score is
        abs_compound = abs(compound)
        if abs_compound >= 0.7:
            confidence = "High"
        elif abs_compound >= 0.3:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        # Build detailed analysis
        sentiment_breakdown = {
            "positive_score": f"{positive:.3f}",
            "neutral_score": f"{neutral:.3f}", 
            "negative_score": f"{negative:.3f}",
            "compound_score": f"{compound:.3f}"
        }
        
        warnings = []
        if len(text.strip()) < 5:
            warnings.append("Very short text - sentiment analysis may be unreliable")
        if abs_compound < 0.1:
            warnings.append("Weak sentiment signal - interpretation should be cautious")
        
        return AnalysisResult(
            label=label,
            score=score,
            model_name="VADER Sentiment",
            model_version="3.3.2",
            is_demo=False,
            details={
                "sentiment": label,
                "confidence": confidence,
                "description": description,
                "text_length": len(text),
                "sentiment_breakdown": sentiment_breakdown,
                "analysis": f"VADER lexicon-based analysis with compound score {compound:.3f}",
                "model_type": "Lexicon and rule-based sentiment analysis optimized for social media"
            },
            warnings=warnings
        )
        
    except Exception as e:
        return AnalysisResult(
            label="Error",
            score=0.0,
            model_name="VADER Sentiment",
            model_version="3.3.2",
            is_demo=False,
            details={
                "error": f"Analysis failed: {str(e)}",
                "text_length": len(text)
            },
            warnings=[
                f"Analysis error: {str(e)}",
                "Could not complete sentiment analysis"
            ]
        )
