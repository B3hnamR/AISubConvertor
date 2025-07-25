import pysrt
from typing import List, Dict, Any
import logging
import os
from datetime import timedelta
from .timing_manager import SubtitleTimingManager

logger = logging.getLogger(__name__)

class SRTParser:
    """Parser for SRT subtitle files with precise timing management"""
    
    def __init__(self):
        self.subtitles = None
        self.original_encoding = 'utf-8'
        self.timing_manager = SubtitleTimingManager()
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse SRT file and return list of subtitle entries with precise timing"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    self.subtitles = pysrt.open(file_path, encoding=encoding)
                    self.original_encoding = encoding
                    logger.info(f"Successfully parsed SRT file with encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if self.subtitles is None:
                raise Exception("Could not parse SRT file with any supported encoding")
            
            # Convert to our internal format with precise timing
            parsed_subtitles = []
            for i, subtitle in enumerate(self.subtitles):
                # تولید خط تایمینگ
                timing_line = f"{self._time_to_string(subtitle.start)} --> {self._time_to_string(subtitle.end)}"
                
                # تجزیه دقیق تایمینگ
                timing_info = self.timing_manager.parse_timing_line(timing_line)
                
                subtitle_entry = {
                    'index': subtitle.index,
                    'start_time': self._time_to_string(subtitle.start),
                    'end_time': self._time_to_string(subtitle.end),
                    'text': subtitle.text.replace('\n', ' ').strip(),  # Clean up line breaks
                    'original_text': subtitle.text,  # Keep original for reference
                    'timing_info': timing_info,  # اطلاعات دقیق تایمینگ
                    'original_timing_line': timing_line  # خط تایمینگ اصلی
                }
                
                parsed_subtitles.append(subtitle_entry)
            
            # اعتبارسنجی تایمینگ
            timing_errors = self.timing_manager.validate_timing_sequence(parsed_subtitles)
            if timing_errors:
                logger.warning(f"Timing validation found {len(timing_errors)} issues")
                for error in timing_errors[:5]:  # نمایش 5 خطای اول
                    logger.warning(f"Timing issue: {error}")
            
            # تحلیل آماری
            timing_stats = self.timing_manager.analyze_timing_statistics(parsed_subtitles)
            logger.info(f"Timing analysis: {timing_stats.get('total_subtitles', 0)} subtitles, "
                       f"duration: {timing_stats.get('total_duration_formatted', 'unknown')}")
            
            logger.info(f"Parsed {len(parsed_subtitles)} subtitle entries with precise timing")
            return parsed_subtitles
            
        except Exception as e:
            logger.error(f"Failed to parse SRT file: {str(e)}")
            raise Exception(f"SRT parsing failed: {str(e)}")
    
    def create_srt_content(self, subtitles: List[Dict[str, Any]]) -> str:
        """Create SRT content from subtitle entries"""
        try:
            srt_content = []
            
            for subtitle in subtitles:
                srt_entry = f"{subtitle['index']}\n"
                srt_entry += f"{subtitle['start_time']} --> {subtitle['end_time']}\n"
                srt_entry += f"{subtitle['text']}\n\n"
                srt_content.append(srt_entry)
            
            return ''.join(srt_content)
            
        except Exception as e:
            logger.error(f"Failed to create SRT content: {str(e)}")
            raise Exception(f"SRT creation failed: {str(e)}")
    
    def save_srt_file(self, subtitles: List[Dict[str, Any]], output_path: str) -> str:
        """Save subtitles to SRT file"""
        try:
            srt_content = self.create_srt_content(subtitles)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"SRT file saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save SRT file: {str(e)}")
            raise Exception(f"SRT save failed: {str(e)}")
    
    def _time_to_string(self, time_obj) -> str:
        """Convert pysrt time object to string format"""
        return f"{time_obj.hours:02d}:{time_obj.minutes:02d}:{time_obj.seconds:02d},{time_obj.milliseconds:03d}"
    
    def validate_srt_file(self, file_path: str) -> bool:
        """Validate if file is a proper SRT file"""
        try:
            if not file_path.lower().endswith('.srt'):
                return False
            
            if not os.path.exists(file_path):
                return False
            
            # Try to parse a few lines to validate format
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # Read first 500 chars
                
            # Basic SRT format validation
            lines = content.strip().split('\n')
            if len(lines) < 3:
                return False
            
            # Check if first line is a number (subtitle index)
            try:
                int(lines[0].strip())
            except ValueError:
                return False
            
            # Check if second line contains time format
            if '-->' not in lines[1]:
                return False
            
            return True
            
        except Exception:
            return False