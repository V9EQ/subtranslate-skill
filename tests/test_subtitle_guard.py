"""Deterministic guard tests, not an assessment of LLM translation quality."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "subtitle-translation/scripts/subtitle_guard.py"
spec = importlib.util.spec_from_file_location("subtitle_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)

SRT = ("\ufeff7\r\n00:00:01,000 --> 00:00:03,000\r\n"
       "<i>Aiden</i> &amp; Rose.\r\nGo to Black Hollow.\r\n\r\n"
       "7\r\n00:00:02,000 --> 00:00:04,500\r\n- I don't know.\r\n- Maybe.\r\n")
VTT = ("WEBVTT demo\nKind: captions\nLanguage: en\n\n"
       "STYLE\n::cue { color: lime; }\n\n"
       "REGION\nid:fred\nwidth:40%\n\n"
       "NOTE preserve me\nThis is not dialogue.\n\n"
       "opening\n00:01.000 --> 00:03.000 position:10% align:start\n"
       "<v Aiden><i>Rose</i> <00:02.000>wait.</v>\n\n"
       "00:03.000 --> 00:04.000\nBlack Hollow.\n")


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def setup_source(self, content=SRT, suffix="srt"):
        self.source = self.root / f"input.{suffix}"
        self.source.write_bytes(content.encode("utf-8"))
        self.manifest = self.root / "source.json"
        guard.extract(self.source, self.manifest)
        manifest = json.loads(self.manifest.read_text())
        self.document = {"source_sha256": manifest["source_sha256"],
                         "translations": copy.deepcopy(manifest["cues"])}
        self.translations = self.root / "translations.json"
        self.target = self.root / f"translated.{suffix}"

    def render(self):
        self.translations.write_text(json.dumps(self.document, ensure_ascii=False), encoding="utf-8")
        return guard.render(self.source, self.translations, self.target)

    def rejected(self, message=None):
        with self.assertRaises(guard.GuardError) as caught:
            self.render()
        if message:
            self.assertIn(message, str(caught.exception))
        self.assertFalse(self.target.exists())

    def test_srt_identity_bom_crlf_duplicate_indices_overlap(self):
        self.setup_source()
        self.assertEqual(self.render(), 2)
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())
        self.assertEqual(guard.verify(self.source, self.target), 2)

    def test_real_translation(self):
        self.setup_source()
        self.document["translations"][0]["text"] = (
            "⟦P0000⟧Эйден⟦P0001⟧ ⟦P0002⟧ Роуз.\nИди в Чёрную Лощину.")
        self.document["translations"][1]["text"] = "- Я не знаю.\n- Возможно."
        self.render()
        self.assertEqual(guard.verify(self.source, self.target), 2)
        self.assertIn("Иди в Чёрную Лощину.".encode(), self.target.read_bytes())

    def test_vtt_metadata_voice_inline_timestamps(self):
        self.setup_source(VTT, "vtt")
        self.render()
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())

    def test_mixed_endings_preserved(self):
        self.setup_source(SRT.replace("Go to Black Hollow.\r\n", "Go to Black Hollow.\n"))
        self.render()
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())

    def test_no_final_newline(self):
        self.setup_source(SRT.rstrip("\r\n"))
        self.render()
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())

    def test_overrides_entities(self):
        self.setup_source("1\n00:00:00,000 --> 00:00:01,000\n{\\an8}Hi &#39;Rose&#39;!\n")
        self.render()
        self.assertEqual(self.source.read_bytes(), self.target.read_bytes())

    def test_missing_duplicate_reordered_extra_ids(self):
        self.setup_source()
        original = copy.deepcopy(self.document)
        variants = [original["translations"][:1], original["translations"] * 2,
                    original["translations"][::-1],
                    original["translations"] + [{"id": "c999999", "text": "Extra"}]]
        for entries in variants:
            with self.subTest(entries=entries):
                self.document["translations"] = entries
                self.rejected("Cue IDs")

    def test_fingerprint(self):
        self.setup_source()
        self.source.write_bytes(self.source.read_bytes().replace(b"Aiden", b"Ayden"))
        self.rejected("fingerprint")

    def test_missing_duplicate_reordered_placeholder(self):
        self.setup_source()
        original = self.document["translations"][0]["text"]
        variants = [original.replace("⟦P0000⟧", ""), original + "⟦P0000⟧",
                    original.replace("⟦P0000⟧", "⟦P0001⟧"), original + "⟦P9999⟧"]
        for text in variants:
            self.document["translations"][0]["text"] = text
            self.rejected("placeholders")

    def test_placeholder_cannot_move_to_another_line(self):
        self.setup_source()
        text = self.document["translations"][0]["text"]
        self.document["translations"][0]["text"] = text.replace("⟦P0002⟧", "") + "⟦P0002⟧"
        self.rejected("placeholders")

    def test_newlines_and_injection(self):
        self.setup_source()
        original = self.document["translations"][1]["text"]
        for text in ["Only one line", original + "\nextra", "\nBlank", original + "<b>x</b>",
                     original + " &amp;", original + " --> x", original + "\x00",
                     original + "\r", original + "\u2028", original + "{\\an8}"]:
            with self.subTest(text=text):
                self.document["translations"][1]["text"] = text
                self.rejected()

    def test_refuse_existing_destinations(self):
        self.setup_source()
        self.target.write_bytes(b"Do not replace")
        with self.assertRaises(FileExistsError):
            self.render()
        self.assertEqual(self.target.read_bytes(), b"Do not replace")
        with self.assertRaises(FileExistsError):
            guard.extract(self.source, self.manifest)

    def test_verify_timing_identifier_metadata_tag_and_line_changes(self):
        self.setup_source(VTT, "vtt")
        variants = [VTT.replace("00:01.000", "00:01.100"),
                    VTT.replace("opening", "changed"),
                    VTT.replace("preserve me", "changed"),
                    VTT.replace("align:start", "align:end"),
                    VTT.replace("<i>", "<b>"),
                    VTT.replace("Black Hollow.", "Black\nHollow.")]
        for text in variants:
            self.target.write_bytes(text.encode())
            with self.assertRaises(guard.GuardError):
                guard.verify(self.source, self.target)

    def test_malformed_unsupported_empty_sources(self):
        variants = [("input.srt", b""), ("input.ass", SRT.encode()),
                    ("input.srt", b"1\n00:00:01,000 --> 00:00:00,000\nHi"),
                    ("input.srt", b"1\n00:60:01,000 --> 00:60:02,000\nHi"),
                    ("input.srt", b"1\n00:00:01,000 --> 00:00:02,000\n"),
                    ("input.srt", b"\xff\xfe1"),
                    ("input.vtt", b"WEBVTT\n00:01.000 --> 00:02.000\nHi"),
                    ("input.vtt", b"not WEBVTT\n\n00:01.000 --> 00:02.000\nHi"),
                    ("input.srt", SRT.replace("Aiden", "⟦P0000⟧").encode()),
                    ("input.srt", SRT.replace("Aiden", "Ai\u2028den").encode())]
        for name, data in variants:
            with self.subTest(name=name, data=data):
                path = self.root / name
                path.write_bytes(data)
                with self.assertRaises(guard.GuardError):
                    guard.parse(path)

    def test_duplicate_json_keys(self):
        self.setup_source()
        self.translations.write_text('{"source_sha256":"a","source_sha256":"b"}')
        with self.assertRaisesRegex(guard.GuardError, "Duplicate JSON key"):
            guard.render(self.source, self.translations, self.target)

    def test_bad_json_shapes(self):
        self.setup_source()
        for document in [[], None, {"source_sha256": self.document["source_sha256"],
                                   "translations": [None]}]:
            self.document = document
            self.rejected()


if __name__ == "__main__":
    unittest.main()
