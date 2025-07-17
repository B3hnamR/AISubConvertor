import re
from typing import List, Dict, Any, Tuple
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

class SubtitleTimingManager:
    """
    مدیریت دقیق تایمینگ زیرنویس‌ها
    اطمینان از حفظ کامل زمان‌بندی و فقط ترجمه متن
    """
    
    def __init__(self):
        # الگوی زمان SRT: 00:00:01,000 --> 00:00:04,000
        self.time_pattern = re.compile(
            r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
        )
        
        # الگوی شماره زیرنویس
        self.index_pattern = re.compile(r'^\d+$')
    
    def parse_timing_line(self, timing_line: str) -> Dict[str, Any]:
        """
        تجزیه خط زمان‌بندی SRT
        
        Args:
            timing_line: خط زمان‌بندی مثل "00:00:01,000 --> 00:00:04,000"
            
        Returns:
            دیکشنری حاوی اطلاعات زمان‌بندی
        """
        try:
            match = self.time_pattern.match(timing_line.strip())
            if not match:
                raise ValueError(f"Invalid timing format: {timing_line}")
            
            groups = match.groups()
            
            start_time = {
                'hours': int(groups[0]),
                'minutes': int(groups[1]),
                'seconds': int(groups[2]),
                'milliseconds': int(groups[3])
            }
            
            end_time = {
                'hours': int(groups[4]),
                'minutes': int(groups[5]),
                'seconds': int(groups[6]),
                'milliseconds': int(groups[7])
            }
            
            return {
                'original_line': timing_line.strip(),
                'start_time': start_time,
                'end_time': end_time,
                'duration_ms': self._calculate_duration(start_time, end_time)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse timing line: {timing_line} - {str(e)}")
            raise ValueError(f"Invalid timing format: {timing_line}")
    
    def _calculate_duration(self, start_time: Dict, end_time: Dict) -> int:
        """محاسبه مدت زمان به میلی‌ثانیه"""
        start_ms = (
            start_time['hours'] * 3600000 +
            start_time['minutes'] * 60000 +
            start_time['seconds'] * 1000 +
            start_time['milliseconds']
        )
        
        end_ms = (
            end_time['hours'] * 3600000 +
            end_time['minutes'] * 60000 +
            end_time['seconds'] * 1000 +
            end_time['milliseconds']
        )
        
        return end_ms - start_ms
    
    def format_timing_line(self, timing_info: Dict[str, Any]) -> str:
        """
        تولید خط زمان‌بندی از اطلاعات تایمینگ
        
        Args:
            timing_info: اطلاعات تایمینگ
            
        Returns:
            خط زمان‌بندی فرمت شده
        """
        try:
            start = timing_info['start_time']
            end = timing_info['end_time']
            
            start_str = f"{start['hours']:02d}:{start['minutes']:02d}:{start['seconds']:02d},{start['milliseconds']:03d}"
            end_str = f"{end['hours']:02d}:{end['minutes']:02d}:{end['seconds']:02d},{end['milliseconds']:03d}"
            
            return f"{start_str} --> {end_str}"
            
        except Exception as e:
            logger.error(f"Failed to format timing: {str(e)}")
            # بازگشت به فرمت اصلی در صورت خطا
            return timing_info.get('original_line', '00:00:00,000 --> 00:00:01,000')
    
    def validate_timing_sequence(self, subtitles: List[Dict[str, Any]]) -> List[str]:
        """
        اعتبارسنجی توالی زمان‌بندی زیرنویس‌ها
        
        Args:
            subtitles: لیست زیرنویس‌ها
            
        Returns:
            لیست خطاهای یافت شده
        """
        errors = []
        
        for i, subtitle in enumerate(subtitles):
            try:
                timing = subtitle.get('timing_info')
                if not timing:
                    errors.append(f"Subtitle {i+1}: Missing timing information")
                    continue
                
                # بررسی مدت زمان مثبت
                if timing['duration_ms'] <= 0:
                    errors.append(f"Subtitle {i+1}: Invalid duration ({timing['duration_ms']}ms)")
                
                # بررسی تداخل با زیرنویس بعدی
                if i < len(subtitles) - 1:
                    next_timing = subtitles[i+1].get('timing_info')
                    if next_timing:
                        current_end = self._time_to_ms(timing['end_time'])
                        next_start = self._time_to_ms(next_timing['start_time'])
                        
                        if current_end > next_start:
                            errors.append(f"Subtitle {i+1}: Overlaps with subtitle {i+2}")
                
            except Exception as e:
                errors.append(f"Subtitle {i+1}: Validation error - {str(e)}")
        
        return errors
    
    def _time_to_ms(self, time_dict: Dict) -> int:
        """تبدیل زمان به میلی‌ثانیه"""
        return (
            time_dict['hours'] * 3600000 +
            time_dict['minutes'] * 60000 +
            time_dict['seconds'] * 1000 +
            time_dict['milliseconds']
        )
    
    def preserve_timing_in_translation(self, original_subtitles: List[Dict], translated_texts: List[str]) -> List[Dict]:
        """
        حفظ تایمینگ اصلی در ترجمه
        
        Args:
            original_subtitles: زیرنویس‌های اصلی با تایمینگ
            translated_texts: متن‌های ترجمه شده
            
        Returns:
            زیرنویس‌های ترجمه شده با تایمینگ حفظ شده
        """
        if len(original_subtitles) != len(translated_texts):
            raise ValueError("Number of original subtitles and translated texts must match")
        
        translated_subtitles = []
        
        for i, (original, translated_text) in enumerate(zip(original_subtitles, translated_texts)):
            try:
                # کپی کامل اطلاعات اصلی
                translated_subtitle = original.copy()
                
                # فقط متن را تغییر می‌دهیم
                translated_subtitle['text'] = translated_text.strip()
                translated_subtitle['translated'] = True
                translated_subtitle['translation_index'] = i
                
                # حفظ کامل تایمینگ اصلی
                if 'timing_info' in original:
                    translated_subtitle['timing_info'] = original['timing_info'].copy()
                
                # حفظ شماره اصلی
                if 'index' in original:
                    translated_subtitle['index'] = original['index']
                
                translated_subtitles.append(translated_subtitle)
                
            except Exception as e:
                logger.error(f"Failed to preserve timing for subtitle {i+1}: {str(e)}")
                # در صورت خطا، حداقل متن ترجمه شده را حفظ کن
                fallback_subtitle = {
                    'index': i + 1,
                    'text': translated_text.strip(),
                    'start_time': original.get('start_time', '00:00:00,000'),
                    'end_time': original.get('end_time', '00:00:01,000'),
                    'translated': True,
                    'error': str(e)
                }
                translated_subtitles.append(fallback_subtitle)
        
        return translated_subtitles
    
    def analyze_timing_statistics(self, subtitles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        تحلیل آماری تایمینگ زیرنویس‌ها
        
        Args:
            subtitles: لیست زیرنویس‌ها
            
        Returns:
            آمار تایمینگ
        """
        if not subtitles:
            return {'error': 'No subtitles provided'}
        
        durations = []
        gaps = []
        total_duration = 0
        
        for i, subtitle in enumerate(subtitles):
            timing = subtitle.get('timing_info')
            if timing:
                duration = timing['duration_ms']
                durations.append(duration)
                total_duration += duration
                
                # محاسبه فاصله با زیرنویس بعدی
                if i < len(subtitles) - 1:
                    next_timing = subtitles[i+1].get('timing_info')
                    if next_timing:
                        current_end = self._time_to_ms(timing['end_time'])
                        next_start = self._time_to_ms(next_timing['start_time'])
                        gap = next_start - current_end
                        gaps.append(gap)
        
        if not durations:
            return {'error': 'No valid timing information found'}
        
        return {
            'total_subtitles': len(subtitles),
            'total_duration_ms': total_duration,
            'total_duration_formatted': self._ms_to_time_string(total_duration),
            'average_duration_ms': sum(durations) / len(durations),
            'min_duration_ms': min(durations),
            'max_duration_ms': max(durations),
            'average_gap_ms': sum(gaps) / len(gaps) if gaps else 0,
            'overlapping_subtitles': len([g for g in gaps if g < 0]),
            'timing_errors': len(self.validate_timing_sequence(subtitles))
        }
    
    def _ms_to_time_string(self, milliseconds: int) -> str:
        """تبدیل میلی‌ثانیه به رشته زمان"""
        hours = milliseconds // 3600000
        minutes = (milliseconds % 3600000) // 60000
        seconds = (milliseconds % 60000) // 1000
        ms = milliseconds % 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"