"""Tests for the audit heuristics (re quran/quran.com-frontend-next#3282)."""
import unittest

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit import check_h1, check_h2, check_h3_pagenum, check_h4_double_punct

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

    def test_h1_ellipsis_continuation(self):
        self.assertEqual(check_h1("Il part... alors Allah sait."), [])
        self.assertEqual(check_h1("Il part… alors Allah sait."), [])

    def test_h1_cyrillic(self):
        self.assertTrue(check_h1("Воистину, Мы сделали это. ивыявить лучшее."))
        self.assertEqual(check_h1("Сказал он, т.е. это пояснение."), [])

    def test_h2_balanced(self):
        self.assertEqual(check_h2("See (i.e. the fathers) here."), [])

    def test_h2_unbalanced(self):
        self.assertTrue(check_h2("he [i.e. the chief) may know"))
        self.assertTrue(check_h2("text with <sup foot_note remainder"))

    def test_h2_sup_tags_balanced(self):
        # Well-formed footnote markers must not flag.
        self.assertEqual(
            check_h2('Joseph said:<sup foot_note="178470">1</sup> "Go."'), [])

    def test_h3_pagenum_residue(self):
        self.assertEqual(check_h3_pagenum("Omniscient 266]."), ["266]"])
        self.assertEqual(check_h3_pagenum("normal [12] text."), [])

    def test_h4_double_punct(self):
        self.assertEqual(check_h4_double_punct("ces noms;."), [";."])
        self.assertEqual(check_h4_double_punct("wait... then."), [])
        self.assertEqual(check_h4_double_punct("end… then."), [])

    def test_h2_sup_tags_unquoted(self):
        # Some resources (e.g. French Hamidullah) omit attribute quotes.
        self.assertEqual(
            check_h2('Voici le Livre.<sup foot_note=211623>1</sup>'), [])


if __name__ == "__main__":
    unittest.main()
