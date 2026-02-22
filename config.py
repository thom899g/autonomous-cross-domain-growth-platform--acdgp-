"""
Configuration manager for ACDGP with environment-aware settings.
Architecture Choice: Centralized config prevents scattered hardcoded values
and enables easy environment switching.
"""
import os
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "acdgp-default")
    credentials_path: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./service-account-key.json")
    firestore_collection: str = "acdgp_modules"
    compatibility_collection: str = "compatibility_assessments"
    integrations_collection: str = "integrated_systems"
    
    def validate(self) -> bool:
        """Validate critical Firebase configuration"""
        if not self.project_id:
            raise ValueError("FIREBASE_PROJECT_ID must be set")
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"Firebase credentials not found at {self.credentials_path}")
        return True

@dataclass
class ModuleConfig:
    """Module discovery and analysis configuration"""
    supported_domains: tuple = ("data_processing", "ml_models", "apis", "storage", "analytics")
    max_modules_per_scan: int = 100
    compatibility_threshold: float = 0.7
    scan_interval_minutes: int = 30
    
@dataclass
class LoggingConfig:
    """Structured logging configuration"""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "./logs/acdgp.log"
    
    def setup_directories(self):
        """Ensure log directory exists"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

class ACDGPConfig:
    """Main configuration aggregator"""
    def __init__(self):
        self.firebase = FirebaseConfig()
        self.modules = ModuleConfig()
        self.logging = LoggingConfig()
        self.validate_all()
    
    def validate_all(self):
        """Validate all configurations"""
        self.firebase.validate()
        self.logging.setup_directories()
        
# Global configuration instance
CONFIG = ACDGPConfig()