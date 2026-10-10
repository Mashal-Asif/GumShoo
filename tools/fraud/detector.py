"""
Fraud Detection Detector

Real ML-based fraud detection using trained scikit-learn model.
Trained on SMS Spam Collection dataset with TF-IDF features.
"""

import joblib
from pathlib import Path

from core.schema import AnalysisResult


# Load the trained fraud detection model
MODEL_PATH = Path(__file__).parent.parent.parent / "fraud_detection" / "sms_fraud_model.pkl"

try:
    _fraud_model = joblib.load(MODEL_PATH)
    _model_available = True
    _model_error = None
except Exception as e:
    _fraud_model = None
    _model_available = False
    _model_error = str(e)


def detect_fraud(text: str) -> AnalysisResult:
    """
    Analyze text for fraud indicators using trained ML model.
    
    Uses a scikit-learn pipeline with TF-IDF features (word 1-2 grams + 
    character 2-4 grams) and Logistic Regression classifier trained on
    SMS Spam Collection dataset.
    
    Args:
        text: Text content to analyze for fraud indicators
    
    Returns:
        AnalysisResult with real ML-based fraud analysis
    
    Example:
        >>> result = detect_fraud("Click here to claim your prize!")
        >>> result.is_demo
        False
        >>> result.label in ["Fraud", "Legit"]
        True
    """
    if not _model_available:
        # Fallback to basic analysis if model unavailable
        return AnalysisResult(
            label="Error",
            score=0.0,
            model_name="SMS Fraud Classifier",
            model_version="1.0.0",
            is_demo=False,
            details={
                "error": f"Model not available: {_model_error}",
                "text_length": len(text)
            },
            warnings=[
                f"Model loading failed: {_model_error}",
                "Cannot perform fraud analysis without trained model"
            ]
        )
    
    try:
        # Get probability scores from the trained model
        probabilities = _fraud_model.predict_proba([text])[0]
        fraud_probability = probabilities[1]  # Index 1 is fraud/spam class
        
        # Determine label and confidence
        if fraud_probability >= 0.5:
            label = "Fraud"
            confidence_desc = "High" if fraud_probability >= 0.8 else "Medium"
        else:
            label = "Legit" 
            confidence_desc = "High" if fraud_probability <= 0.2 else "Medium"
        
        # Get feature information (top TF-IDF features if available)
        try:
            # Try to get some feature insights
            tfidf_step = _fraud_model.named_steps['tfidf']
            features = tfidf_step.transform([text])
            feature_names = tfidf_step.get_feature_names_out()
            
            # Get top features for this text
            feature_scores = features.toarray()[0]
            top_indices = feature_scores.argsort()[-10:][::-1]
            top_features = [feature_names[i] for i in top_indices if feature_scores[i] > 0][:5]
            
            analysis_details = f"Key features: {', '.join(top_features[:3])}" if top_features else "Standard text analysis"
            
        except:
            analysis_details = "TF-IDF feature analysis completed"
            top_features = []
        
        return AnalysisResult(
            label=label,
            score=fraud_probability,
            model_name="SMS Fraud Classifier",
            model_version="1.0.0",
            is_demo=False,
            details={
                "verdict": f"{label} ({confidence_desc} confidence)",
                "fraud_probability": f"{fraud_probability:.3f}",
                "legitimate_probability": f"{1 - fraud_probability:.3f}",
                "text_length": len(text),
                "analysis": analysis_details,
                "model_type": "Logistic Regression with TF-IDF features",
                "training_data": "SMS Spam Collection dataset"
            },
            warnings=[] if fraud_probability < 0.9 else [
                "Very high fraud probability detected - exercise extreme caution"
            ]
        )
        
    except Exception as e:
        return AnalysisResult(
            label="Error",
            score=0.0,
            model_name="SMS Fraud Classifier", 
            model_version="1.0.0",
            is_demo=False,
            details={
                "error": f"Prediction failed: {str(e)}",
                "text_length": len(text)
            },
            warnings=[
                f"Analysis error: {str(e)}",
                "Could not complete fraud detection"
            ]
        )
