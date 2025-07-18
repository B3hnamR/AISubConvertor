from abc import ABC, abstractmethod
from typing import List, Dict, Any
import hashlib
from cachetools import TTLCache, cachedmethod

class BaseTranslator(ABC):
    """Base class for all translation providers with caching"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # Cache for 1 hour
    
    def _get_cache_key(self, text: str, target_language: str) -> str:
        """Generate cache key"""
        return hashlib.md5(f"{text}_{target_language}".encode()).hexdigest()
    
    @cachedmethod(lambda self: self.cache, key=lambda self, text, target_language: self._get_cache_key(text, target_language))
    async def translate_text(self, text: str, target_language: str = "Persian") -> str:
        """Translate a single text string with caching"""
        return await self._translate_text_impl(text, target_language)
    
    @abstractmethod
    async def _translate_text_impl(self, text: str, target_language: str) -> str:
        """Implementation of text translation"""
        pass
    
    async def translate_batch(self, texts: List[str], target_language: str = "Persian") -> List[str]:
        """Translate multiple text strings in batch with caching"""
        translated = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            key = self._get_cache_key(text, target_language)
            if key in self.cache:
                translated.append(self.cache[key])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        if uncached_texts:
            batch_translated = await self._translate_batch_impl(uncached_texts, target_language)
            for idx, trans in zip(uncached_indices, batch_translated):
                key = self._get_cache_key(texts[idx], target_language)
                self.cache[key] = trans
                translated.insert(idx, trans)  # Note: this assumes translated is built in order
        
        return translated
    
    @abstractmethod
    async def _translate_batch_impl(self, texts: List[str], target_language: str) -> List[str]:
        """Implementation of batch translation"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the translation provider"""
        pass