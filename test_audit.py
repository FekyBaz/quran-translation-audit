"""Tests for the audit heuristics (re quran/quran.com-frontend-next#3282)."""
import unittest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import check_h1, check_h2

LEAK_3189 = ("To Allah belongs the dominion of the heavens and the earth; "
             "and Allah is All-Powerful. indeed been successful.")
GOOD_BASMALAH = ("In the name of Allah, the Most Merciful, "
                 "the Most Compassionate.")
GOOD_STYLE = ("They pray to Allah: 'Our Lord! Do not let our hearts swerve.")


class TestHeuristics(unittest.TestCase):
    def test_h1_catches_known_leak(self):
        hits = check_h1(LEAK_3189)
        self.assertTrue(hits, "3:189 leak must be flagged")
        self.assertTrue(any("indeed been" in h for h in hits))

    def test_h1_clean_verse(self):
        self.assertEqual(check_h1(GOOD_BASMALAH), [])

    def test_h1_ignores_abbreviations(self):
        self.assertEqual(check_h1("He said, e.g. this is fine."), [])

    def test_h2_balanced(self):
        self.assertEqual(check_h2("See (i.e. the fathers) here."), [])

    def test_h2_unbalanced(self):
        self.assertTrue(check_h2("he [i.e. the chief) may know"))
        self.assertTrue(check_h2("text with <sup foot_note remainder"))

    def test_h2_sup_tags_balanced(self):
        # Well-formed footnote markers must not flag.
        self.assertEqual(
            check_h2('Joseph said:<sup foot_note="178470">1</sup> "Go."'), [])


if __name__ == "__main__":
    unittest.main()
