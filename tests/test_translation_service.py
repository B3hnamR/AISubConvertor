import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.translation_service import TranslationService
from src.utils import TranslationError, FileProcessingError

@pytest.fixture
def mock_dependencies():
    with patch('src.services.translation_service.SRTParser') as mock_parser, \
         patch('src.services.translation_service.SubtitleTimingManager') as mock_timing, \
         patch('src.services.translation_service.get_file_manager') as mock_file_manager, \
         patch('src.services.translation_service.TranslatorFactory') as mock_factory, \
         patch('src.services.translation_service.get_dynamic_settings') as mock_dynamic, \
         patch('src.services.translation_service.get_error_handler') as mock_error_handler, \
         patch('src.services.translation_service.InputValidator') as mock_validator:
        
        mock_translator = AsyncMock()
        mock_translator.translate_batch = AsyncMock(return_value=["translated text"])
        mock_factory.create_translator.return_value = mock_translator
        
        yield {
            'parser': mock_parser,
            'timing': mock_timing,
            'file_manager': mock_file_manager,
            'factory': mock_factory,
            'dynamic': mock_dynamic,
            'error_handler': mock_error_handler,
            'validator': mock_validator
        }

@pytest.mark.asyncio
async def test_translate_subtitle_file_success(mock_dependencies):
    service = TranslationService()
    
    mock_dependencies['parser'].return_value.parse_file.return_value = [{
        'text': 'original',
        'start_time': '00:00:00,000',
        'end_time': '00:00:01,000'
    }]
    mock_dependencies['parser'].return_value.save_srt_file.return_value = "output.srt"
    
    result = await service.translate_subtitle_file("input.srt")
    
    assert result == "output.srt"
    mock_dependencies['parser'].return_value.parse_file.assert_called_once_with("input.srt")

@pytest.mark.asyncio
async def test_translate_subtitle_file_invalid_format(mock_dependencies):
    service = TranslationService()
    mock_dependencies['parser'].return_value.validate_srt_file.return_value = False
    
    with pytest.raises(FileProcessingError):
        await service.translate_subtitle_file("invalid.srt")

@pytest.mark.asyncio
async def test_get_user_preview_success(mock_dependencies):
    service = TranslationService()
    mock_dependencies['file_manager'].return_value.get_user_file_path = AsyncMock(return_value="file.srt")
    mock_dependencies['parser'].return_value.parse_file.return_value = [{
        'text': 'original',
        'start_time': '00:00:00,000',
        'end_time': '00:00:01,000'
    }]
    
    result = await service.get_user_preview(123)
    
    assert len(result) == 1
    assert result[0]['translated'] == "translated text"

@pytest.mark.asyncio
async def test_cleanup_user_data(mock_dependencies):
    service = TranslationService()
    mock_dependencies['file_manager'].return_value.cleanup_user_files = AsyncMock(return_value=True)
    
    result = await service.cleanup_user_data(123)
    assert result is True

@pytest.mark.asyncio
async def test_change_translator_success(mock_dependencies):
    service = TranslationService()
    service.change_translator("new_provider", {})
    mock_dependencies['factory'].create_translator.assert_called_once_with("new_provider", {})

# Run tests
if __name__ == '__main__':
    pytest.main([__file__])