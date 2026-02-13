#!/usr/bin/env python3
"""
Test runner for Sonora video dubbing system validation.

Runs comprehensive tests and validates key metrics:
- Audio extraction accuracy
- Pipeline integration
- Lip-sync accuracy
- Export quality
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add the parent directory to the path so we can import sonora modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_audio_extraction_test():
    """Test audio extraction accuracy."""
    logger.info("🧪 Running audio extraction test...")
    
    try:
        # Run the specific test
        result = pytest.main([
            "sonora/tests/test_video_validation.py::TestAudioExtraction::test_audio_extraction",
            "-v", "--tb=short"
        ])
        
        if result == 0:
            logger.info("✅ Audio extraction test PASSED - Duration matches video duration")
            return True
        else:
            logger.error("❌ Audio extraction test FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Audio extraction test ERROR: {e}")
        return False


def run_pipeline_integration_test():
    """Test pipeline integration."""
    logger.info("🧪 Running pipeline integration test...")
    
    try:
        result = pytest.main([
            "sonora/tests/test_video_validation.py::TestPipelineIntegration::test_pipeline_integration",
            "-v", "--tb=short"
        ])
        
        if result == 0:
            logger.info("✅ Pipeline integration test PASSED - Dubbed audio replaces source")
            return True
        else:
            logger.error("❌ Pipeline integration test FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pipeline integration test ERROR: {e}")
        return False


def run_lipsync_accuracy_test():
    """Test lip-sync accuracy."""
    logger.info("🧪 Running lip-sync accuracy test...")
    
    try:
        result = pytest.main([
            "sonora/tests/test_video_validation.py::TestLipSyncAccuracy::test_lipsync_accuracy",
            "-v", "--tb=short"
        ])
        
        if result == 0:
            logger.info("✅ Lip-sync accuracy test PASSED - Lip movement vs speech offset < 100ms")
            return True
        else:
            logger.error("❌ Lip-sync accuracy test FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Lip-sync accuracy test ERROR: {e}")
        return False


def run_export_quality_test():
    """Test export quality."""
    logger.info("🧪 Running export quality test...")
    
    try:
        result = pytest.main([
            "sonora/tests/test_video_validation.py::TestExportQuality::test_export_quality",
            "-v", "--tb=short"
        ])
        
        if result == 0:
            logger.info("✅ Export quality test PASSED - Resolution + fps match")
            return True
        else:
            logger.error("❌ Export quality test FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Export quality test ERROR: {e}")
        return False


def run_integration_test():
    """Test complete integration."""
    logger.info("🧪 Running complete integration test...")
    
    try:
        result = pytest.main([
            "sonora/tests/test_video_validation.py::TestVideoDubbingIntegration::test_complete_video_dubbing_pipeline",
            "-v", "--tb=short"
        ])
        
        if result == 0:
            logger.info("✅ Integration test PASSED - Complete pipeline works")
            return True
        else:
            logger.error("❌ Integration test FAILED")
            return False
            
    except Exception as e:
        logger.error(f"❌ Integration test ERROR: {e}")
        return False


def check_dependencies():
    """Check if all required dependencies are available."""
    logger.info("🔍 Checking dependencies...")
    
    required_packages = [
        'cv2', 'numpy', 'librosa', 'soundfile', 'ffmpeg', 'moviepy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'ffmpeg':
                import ffmpeg
            else:
                __import__(package)
            logger.info(f"✅ {package} - Available")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"⚠️  {package} - Missing")
    
    if missing_packages:
        logger.error(f"❌ Missing required packages: {', '.join(missing_packages)}")
        logger.error("Install with: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All required dependencies are available")
    return True


def run_all_tests():
    """Run all validation tests."""
    logger.info("🎬 Starting Sonora Video Dubbing System Validation")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    # Check dependencies first
    if not check_dependencies():
        logger.error("❌ Dependency check failed. Cannot run tests.")
        return False
    
    # Run individual tests
    tests = [
        ("Audio Extraction", run_audio_extraction_test),
        ("Pipeline Integration", run_pipeline_integration_test),
        ("Lip-sync Accuracy", run_lipsync_accuracy_test),
        ("Export Quality", run_export_quality_test),
        ("Complete Integration", run_integration_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} Test...")
        results[test_name] = test_func()
    
    # Summary
    total_time = time.time() - start_time
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:20} | {status}")
    
    logger.info("-" * 60)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {passed_tests}")
    logger.info(f"Failed: {total_tests - passed_tests}")
    logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    logger.info(f"Total Time: {total_time:.2f} seconds")
    
    if passed_tests == total_tests:
        logger.info("\n🎉 ALL TESTS PASSED! Video dubbing system is ready.")
        return True
    else:
        logger.error(f"\n⚠️  {total_tests - passed_tests} TESTS FAILED. Check logs above.")
        return False


def main():
    """Main entry point."""
    print("🎬 Sonora Video Dubbing System - Test Runner")
    print("=" * 50)
    print("This script validates the video dubbing system with the following tests:")
    print("1. Audio Extraction - Duration ≈ video duration")
    print("2. Pipeline Integration - Dubbed audio replaces source")
    print("3. Lip-sync Accuracy - Lip movement vs speech offset < 100ms")
    print("4. Export Quality - Resolution + fps match")
    print("5. Complete Integration - End-to-end pipeline")
    print()
    
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The video dubbing system is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the logs and fix any issues.")
        return 1


if __name__ == "__main__":
    exit(main())





































