#!/usr/bin/env python
"""Verification script for keyword_extractor module."""
import sys

try:
    from analyzers.keyword_extractor import extract_keywords, extract_top_skills, extract_resume_keywords
    print("✓ Successfully imported extract_keywords")
    print("✓ Successfully imported extract_top_skills")
    print("✓ Successfully imported extract_resume_keywords")
    print("\nOK - All imports successful")
    sys.exit(0)
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)
