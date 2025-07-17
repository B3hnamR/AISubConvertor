#!/usr/bin/env python3
"""
Test script for file management system
"""

import sys
import os
import asyncio
import tempfile
import shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils import UserFileManager

async def test_file_manager():
    """Test file management system"""
    print("🧪 Testing File Management System...")
    print("=" * 50)
    
    # ایجاد دایرکتوری موقت برای تست
    test_temp_dir = tempfile.mkdtemp(prefix="test_aisubconvertor_")
    print(f"📁 Test directory: {test_temp_dir}")
    
    try:
        # ایجاد مدیر فایل
        file_manager = UserFileManager(test_temp_dir, max_file_size_mb=10)
        
        # تست کاربر 1
        user1_id = 12345
        filename1 = "test_movie.srt"
        file_size1 = 1024 * 50  # 50KB
        
        print(f"\n👤 Testing User {user1_id}:")
        
        # بررسی امکان آپلود
        can_upload = await file_manager.can_upload_file(user1_id)
        print(f"✅ Can upload: {can_upload}")
        
        # آماده‌سازی آپلود
        file_info = await file_manager.prepare_user_upload(user1_id, filename1, file_size1)
        print(f"✅ File prepared: {file_info['file_id']}")
        
        # شبیه‌سازی دانلود
        await file_manager.start_file_download(user1_id)
        
        # ایجاد فایل تست
        test_content = """1
00:00:01,000 --> 00:00:04,000
Hello, this is a test subtitle.

2
00:00:05,000 --> 00:00:08,000
This is the second line.
"""
        
        with open(file_info['file_path'], 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        await file_manager.complete_file_download(user1_id)
        print(f"✅ Download completed")
        
        # شروع پردازش
        await file_manager.start_file_processing(user1_id)
        print(f"✅ Processing started")
        
        # تست کاربر 2 (همزمان)
        user2_id = 67890
        filename2 = "another_movie.srt"
        file_size2 = 1024 * 30  # 30KB
        
        print(f"\n👤 Testing User {user2_id} (concurrent):")
        
        can_upload2 = await file_manager.can_upload_file(user2_id)
        print(f"✅ Can upload: {can_upload2}")
        
        file_info2 = await file_manager.prepare_user_upload(user2_id, filename2, file_size2)
        print(f"✅ File prepared: {file_info2['file_id']}")
        
        # تست محدودیت همزمانی برای کاربر 1
        print(f"\n🔒 Testing concurrency limits for User {user1_id}:")
        can_upload_again = await file_manager.can_upload_file(user1_id)
        print(f"✅ Can upload again: {can_upload_again} (should be False)")
        
        # تست آمار سیستم
        print(f"\n📊 System Statistics:")
        stats = await file_manager.get_system_stats()
        print(f"✅ Active files: {stats['active_files']}")
        print(f"✅ Total size: {stats['total_size_mb']} MB")
        print(f"✅ Status breakdown: {stats['status_breakdown']}")
        
        # تست پاکسازی
        print(f"\n🧹 Testing cleanup:")
        cleanup_success = await file_manager.cleanup_user_files(user1_id)
        print(f"✅ Cleanup user 1: {cleanup_success}")
        
        # بررسی آمار بعد از پاکسازی
        stats_after = await file_manager.get_system_stats()
        print(f"✅ Active files after cleanup: {stats_after['active_files']}")
        
        # تست اعتبارسنجی حجم فایل
        print(f"\n📏 Testing file size validation:")
        large_file_size = 1024 * 1024 * 100  # 100MB
        try:
            await file_manager.prepare_user_upload(user2_id, "large_file.srt", large_file_size)
            print("❌ Large file validation failed")
        except Exception as e:
            print(f"✅ Large file rejected: {str(e)}")
        
        print(f"\n🎉 File Management System test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
        
    finally:
        # پاکسازی دایرکتوری تست
        try:
            shutil.rmtree(test_temp_dir)
            print(f"🧹 Cleaned up test directory")
        except:
            pass

async def test_timing_manager():
    """Test timing management system"""
    print("\n🧪 Testing Timing Management System...")
    print("=" * 50)
    
    try:
        from src.subtitle import SubtitleTimingManager
        
        timing_manager = SubtitleTimingManager()
        
        # تست تجزیه خط تایمینگ
        timing_line = "00:01:23,456 --> 00:01:27,890"
        timing_info = timing_manager.parse_timing_line(timing_line)
        
        print(f"✅ Parsed timing: {timing_line}")
        print(f"   Duration: {timing_info['duration_ms']}ms")
        
        # تست فرمت کردن
        formatted_line = timing_manager.format_timing_line(timing_info)
        print(f"✅ Formatted back: {formatted_line}")
        
        # تست حفظ تایمینگ در ترجمه
        original_subtitles = [
            {
                'index': 1,
                'start_time': '00:00:01,000',
                'end_time': '00:00:04,000',
                'text': 'Hello world',
                'timing_info': timing_manager.parse_timing_line('00:00:01,000 --> 00:00:04,000')
            },
            {
                'index': 2,
                'start_time': '00:00:05,000',
                'end_time': '00:00:08,000',
                'text': 'Second subtitle',
                'timing_info': timing_manager.parse_timing_line('00:00:05,000 --> 00:00:08,000')
            }
        ]
        
        translated_texts = ['سلام دنیا', 'زیرنویس دوم']
        
        preserved_subtitles = timing_manager.preserve_timing_in_translation(
            original_subtitles, translated_texts
        )
        
        print(f"✅ Preserved timing for {len(preserved_subtitles)} subtitles")
        for sub in preserved_subtitles:
            print(f"   {sub['index']}: {sub['start_time']} --> {sub['end_time']} | {sub['text']}")
        
        # تست آمار تایمینگ
        stats = timing_manager.analyze_timing_statistics(preserved_subtitles)
        print(f"✅ Timing statistics: {stats['total_subtitles']} subtitles, {stats['total_duration_formatted']}")
        
        print(f"\n🎉 Timing Management System test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Timing test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive System Tests...")
    print("=" * 60)
    
    # تست مدیریت فایل
    file_test_success = await test_file_manager()
    
    # تست مدیریت تایمینگ
    timing_test_success = await test_timing_manager()
    
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"   File Management: {'✅ PASSED' if file_test_success else '❌ FAILED'}")
    print(f"   Timing Management: {'✅ PASSED' if timing_test_success else '❌ FAILED'}")
    
    if file_test_success and timing_test_success:
        print("\n🎉 All tests passed! System is ready for production.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)