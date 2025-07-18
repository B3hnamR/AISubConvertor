#!/usr/bin/env python3
"""
Test script for SRT parser functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.subtitle import SRTParser

def test_srt_parser():
    """Test SRT parser with sample file"""
    parser = SRTParser()

    # Test file path
    test_file = os.path.join(os.path.dirname(__file__), '..', 'examples', 'test_subtitle.srt')

    try:
        print("🧪 Testing SRT Parser...")
        print(f"📁 Test file: {test_file}")

        # Validate file
        is_valid = parser.validate_srt_file(test_file)
        print(f"✅ File validation: {'PASSED' if is_valid else 'FAILED'}")

        if not is_valid:
            print("❌ Test file is not valid SRT format")
            return False

        # Parse file
        subtitles = parser.parse_file(test_file)
        print(f"✅ Parsed {len(subtitles)} subtitle entries")

        # Display parsed content
        print("\n📋 Parsed subtitles:")
        for i, subtitle in enumerate(subtitles[:3]):  # Show first 3
            print(f"  {i+1}. [{subtitle['start_time']} --> {subtitle['end_time']}]")
            print(f"     Text: {subtitle['text']}")

        # Test SRT creation
        output_path = os.path.join(os.path.dirname(__file__), 'test_output.srt')
        created_path = parser.save_srt_file(subtitles, output_path)
        print(f"✅ Created SRT file: {created_path}")

        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)
            print("🧹 Cleaned up test file")

        print("\n🎉 SRT Parser test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_srt_parser()
    sys.exit(0 if success else 1)