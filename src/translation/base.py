from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseTranslator(ABC):
    """Base class for all translation providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def translate_text(self, text: str, target_language: str = "Persian") -> str:
        """Translate a single text string"""
        pass
    
    @abstractmethod
    async def translate_batch(self, texts: List[str], target_language: str = "Persian") -> List[str]:
        """Translate multiple text strings in batch"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the translation provider"""
        pass