"""
Settings Management Module

Handles application configuration from YAML files and environment variables.
Settings are immutable after load to prevent accidental modification during runtime.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """
    Immutable application configuration.
    
    Loads settings from config.yaml and environment variables.
    Provides sensible defaults and graceful fallback if configuration
    is missing or invalid.
    
    Attributes:
        max_file_size_mb: Maximum upload file size in megabytes
        max_texts_per_batch: Maximum number of texts to process at once
        url_timeout_seconds: Timeout for URL fetching in seconds
        max_url_size_mb: Maximum size for fetched URLs in megabytes
        models_dir: Directory path for model files
        page_title: Application page title
        page_layout: Streamlit page layout mode
    
    Example:
        >>> settings = Settings.load()
        >>> settings.max_file_size_mb
        10
        >>> settings.page_title
        'GumShoo - Social Media Safety Detector'
    """
    
    max_file_size_mb: int = 10
    max_texts_per_batch: int = 500
    url_timeout_seconds: int = 10
    max_url_size_mb: int = 5
    models_dir: Path = Path("models")
    page_title: str = "GumShoo - Social Media Safety Detector"
    page_layout: str = "centered"
    
    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Settings":
        """
        Load settings from YAML config and environment variables.
        
        Reads configuration from config.yaml if it exists, otherwise
        uses default values. Environment variables from .env are loaded
        but currently not used (reserved for future secrets).
        
        Args:
            config_path: Path to the YAML configuration file
        
        Returns:
            Settings instance with loaded or default configuration
        
        Example:
            >>> settings = Settings.load()
            >>> settings = Settings.load("custom_config.yaml")
        
        Note:
            If config file is missing or invalid, default values are used
            and no error is raised. This ensures the application can always
            start with reasonable defaults.
        """
        # Load environment variables from .env if present
        load_dotenv()
        
        config = {}
        
        # Try to load from YAML config file
        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                    if loaded_config and isinstance(loaded_config, dict):
                        config = loaded_config
            except (yaml.YAMLError, OSError, IOError) as e:
                # If config file is invalid, log warning but continue with defaults
                print(f"Warning: Could not load {config_path}: {e}")
                print("Using default configuration values")
        
        # Convert models_dir to Path if it's a string
        if "models_dir" in config and isinstance(config["models_dir"], str):
            config["models_dir"] = Path(config["models_dir"])
        
        # Create Settings with loaded config or defaults
        try:
            return cls(**config)
        except TypeError as e:
            # If there's an unexpected field in config, use defaults
            print(f"Warning: Invalid configuration fields: {e}")
            print("Using default configuration values")
            return cls()
    
    @property
    def max_file_size_bytes(self) -> int:
        """
        Get maximum file size in bytes.
        
        Returns:
            Maximum file size in bytes
        
        Example:
            >>> settings.max_file_size_bytes
            10485760
        """
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def max_url_size_bytes(self) -> int:
        """
        Get maximum URL content size in bytes.
        
        Returns:
            Maximum URL content size in bytes
        
        Example:
            >>> settings.max_url_size_bytes
            5242880
        """
        return self.max_url_size_mb * 1024 * 1024


# Global settings instance
# Loaded once at module import time
settings = Settings.load()
