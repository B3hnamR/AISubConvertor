from typing import Dict, Any
from .base import BaseTranslator
from .openai_translator import OpenAITranslator

class TranslatorFactory:
    """Factory class for creating translation providers"""
    
    _translators = {
        'openai': OpenAITranslator,
        # Add more translators here in the future
        # 'google': GoogleTranslator,
        # 'azure': AzureTranslator,
    }
    
    @classmethod
    def create_translator(cls, provider: str, config: Dict[str, Any]) -> BaseTranslator:
        """Create a translator instance based on provider name"""
        if provider not in cls._translators:
            available = ', '.join(cls._translators.keys())
            raise ValueError(f"Unknown translator provider: {provider}. Available: {available}")
        
        translator_class = cls._translators[provider]
        return translator_class(config)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available translation providers"""
        return list(cls._translators.keys())
    
    @classmethod
    def register_translator(cls, name: str, translator_class: type):
        """Register a new translator provider"""
        if not issubclass(translator_class, BaseTranslator):
            raise ValueError("Translator class must inherit from BaseTranslator")
        cls._translators[name] = translator_class