"""Tests for the wbw sweep helpers (re quran/quran.com-frontend-next#3317)."""
import unittest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep_wbw import is_pronounceable, parse_chapters


class TestPronounceable(unittest.TestCase):
    def test_ayah_markers_have_no_clip(self):
        # End-of-ayah numerals (112:1 word 5, 114:6 word 4) are not words.
        self.assertFalse(is_pronounceable("١"))
        self.assertFalse(is_pronounceable("٦"))
        self.assertFalse(is_pronounceable(""))
        self.assertFalse(is_pronounceable("۝"))

    def test_real_words_have_clips(self):
        self.assertTrue(is_pronounceable("قُلْ"))
        self.assertTrue(is_pronounceable("ٱللَّهُ"))
        self.assertTrue(is_pronounceable("إِنَّ"))


class TestParseChapters(unittest.TestCase):
    def test_ranges_and_lists(self):
        self.assertEqual(parse_chapters("1-114"), list(range(1, 115)))
        self.assertEqual(parse_chapters("112-114"), [112, 113, 114])
        self.assertEqual(parse_chapters("2,98"), [2, 98])

    def test_out_of_range_dropped(self):
        self.assertEqual(parse_chapters("0,115,98"), [98])


if __name__ == "__main__":
    unittest.main()
