import unittest

from psyr.common import ROOT
from psyr.evaluation.schema import (
    ParseError,
    parse_candidates,
    parse_decision,
)


class CalibrationPromptContractRegressionTests(unittest.TestCase):

    def test_extract_prompt_separates_uncertainty_from_appraisal_value(self):
        text = (
            ROOT / "configs/prompts/extract.txt"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'MUST be exactly "confident" or "uncertain"',
            text,
        )
        self.assertIn(
            '"uncertain_meaning" is NOT an uncertainty value',
            text,
        )

    def test_extract_prompt_forbids_replay_and_guessed_supersedes(self):
        text = (
            ROOT / "configs/prompts/extract.txt"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Every emitted update MUST have source_turn equal to that CURRENT TURN",
            text,
        )
        self.assertIn(
            "NEVER emit an update sourced from an earlier turn",
            text,
        )
        self.assertIn(
            "MUST ALWAYS be [] in this experiment",
            text,
        )
        self.assertIn(
            'The literal key-value pair "supersedes":[] MUST appear',
            text,
        )

    def test_decision_prompt_separates_control_action_and_family(self):
        text = (
            ROOT / "configs/prompts/decide.txt"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "action is a CONTROL decision",
            text,
        )
        self.assertIn(
            'action="proceed" and family="reappraisal"',
            text,
        )

    def test_strict_parser_still_rejects_observed_invalid_outputs(self):

        bad_decision = (
            '{"action":"reappraisal",'
            '"family":"reappraisal",'
            '"targets":{},'
            '"basis":[1]}'
        )

        with self.assertRaises(ParseError):
            parse_decision(bad_decision)

        bad_extract = (
            '{"updates":[{'
            '"field":"appraisal",'
            '"value":"uncertain_meaning",'
            '"source_turn":1,'
            '"quote":"x",'
            '"epistemic":"explicit",'
            '"uncertainty":"uncertain_meaning",'
            '"episode":"e",'
            '"relation":"assert",'
            '"supersedes":[1],'
            '"stance":"user_report"'
            '}]}'
        )

        with self.assertRaises(ParseError):
            parse_candidates(bad_extract)


if __name__ == "__main__":
    unittest.main()
