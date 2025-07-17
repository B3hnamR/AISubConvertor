import openai
from typing import List, Dict, Any
import asyncio
import logging
from .base import BaseTranslator

logger = logging.getLogger(__name__)

class OpenAITranslator(BaseTranslator):
    """OpenAI-based translator using GPT models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=config['api_key'])
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.max_tokens = config.get('max_tokens', 4000)
    
    async def translate_text(self, text: str, target_language: str = "Persian") -> str:
        """Translate a single text string using OpenAI"""
        try:
            prompt = self._create_translation_prompt(text, target_language)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate the given text to {target_language}. Maintain the original meaning and context. Only return the translated text without any additional explanations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content.strip()
            logger.info(f"Successfully translated text: {text[:50]}...")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed for text: {text[:50]}... Error: {str(e)}")
            raise Exception(f"Translation failed: {str(e)}")
    
    async def translate_batch(self, texts: List[str], target_language: str = "Persian") -> List[str]:
        """Translate multiple text strings in batch"""
        try:
            # For better efficiency, we can batch multiple subtitles in one request
            if len(texts) <= 10:  # Small batch - translate together
                return await self._translate_batch_together(texts, target_language)
            else:  # Large batch - translate individually with concurrency
                return await self._translate_batch_concurrent(texts, target_language)
                
        except Exception as e:
            logger.error(f"Batch translation failed: {str(e)}")
            raise Exception(f"Batch translation failed: {str(e)}")
    
    async def _translate_batch_together(self, texts: List[str], target_language: str) -> List[str]:
        """Translate small batches together in one request"""
        numbered_texts = "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
        
        prompt = f"""Translate the following numbered subtitle lines to {target_language}. 
        Maintain the original meaning and context. Return only the translated lines with their numbers:

{numbered_texts}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a professional subtitle translator. Translate to {target_language} maintaining timing and context."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=0.3
        )
        
        translated_content = response.choices[0].message.content.strip()
        
        # Parse the numbered response back to list
        translated_lines = []
        for line in translated_content.split('\n'):
            if line.strip() and '. ' in line:
                translated_text = line.split('. ', 1)[1] if '. ' in line else line
                translated_lines.append(translated_text.strip())
        
        # Ensure we have the same number of translations as inputs
        while len(translated_lines) < len(texts):
            translated_lines.append(texts[len(translated_lines)])  # Fallback to original
            
        return translated_lines[:len(texts)]
    
    async def _translate_batch_concurrent(self, texts: List[str], target_language: str) -> List[str]:
        """Translate large batches with concurrent requests"""
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def translate_with_semaphore(text):
            async with semaphore:
                return await self.translate_text(text, target_language)
        
        tasks = [translate_with_semaphore(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    def _create_translation_prompt(self, text: str, target_language: str) -> str:
        """Create a translation prompt for the given text"""
        return f"Translate this subtitle text to {target_language}: {text}"
    
    def get_provider_name(self) -> str:
        """Return the name of the translation provider"""
        return f"OpenAI ({self.model})"