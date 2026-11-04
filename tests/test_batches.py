"""Bounded windows, early validation, and lossless assembly (no model calls)."""
import copy
import json
import subprocess
import sys
import unittest
import test_subtitle_guard as base
from test_subtitle_guard import SCRIPT, SRT, VTT, guard


class BatchTests(unittest.TestCase):
    setUp = base.GuardTests.setUp
    setup_source = base.GuardTests.setup_source

    def part(self, name, entries, fingerprint=None):
        path = self.root / name
        path.write_text(json.dumps({
            "source_sha256": fingerprint or self.document["source_sha256"],
            "translations": entries,
        }), encoding="utf-8")
        return path

    def test_windows_and_last_batch(self):
        self.setup_source()
        output = self.root / "window.json"
        guard.batch(self.source, output, start=1, count=1)
        window = json.loads(output.read_text())
        self.assertEqual(window["cues"], self.document["translations"][:1])
        self.assertEqual(window["context_before"], [])
        self.assertEqual(window["context_after"], self.document["translations"][1:])
        self.assertEqual(window["next_start"], 2)
        self.assertEqual(window["total_cues"], 2)
        last = self.root / "last.json"
        guard.batch(self.source, last, start=2, count=30)
        window = json.loads(last.read_text())
        self.assertIsNone(window["next_start"])
        self.assertEqual(len(window["cues"]), 1)
        self.assertEqual(len(window["context_before"]), 1)
        with self.assertRaises(FileExistsError):
            guard.batch(self.source, last)

    def test_invalid_ranges(self):
        self.setup_source()
        for options in [{"start": 0}, {"start": 3}, {"count": 0},
                        {"count": -1}, {"context": -1}, {"context": 6}]:
            output = self.root / "invalid.json"
            with self.subTest(options=options), self.assertRaises(guard.GuardError):
                guard.batch(self.source, output, **options)
            self.assertFalse(output.exists())

    def test_check_rejects_overlap_stale_and_bad_placeholders(self):
        self.setup_source()
        entries = self.document["translations"]
        good = self.part("good.json", entries[:1])
        self.assertEqual(guard.check(self.source, good, 1, 1), 1)
        bad_token = copy.deepcopy(entries[:1])
        bad_token[0]["text"] = bad_token[0]["text"].replace("⟦P0000⟧", "")
        for name, content, sha in [("overlap", entries, None),
                                   ("stale", entries[:1], "wrong"),
                                   ("token", bad_token, None),
                                   ("wrong-id", entries[1:], None)]:
            with self.subTest(name=name), self.assertRaises(guard.GuardError):
                guard.check(self.source, self.part(name, content, sha), 1, 1)

    def test_merge_roundtrip_both_formats(self):
        for content, suffix in [(SRT, "srt"), (VTT, "vtt")]:
            # Each format gets a fresh workspace.
            with self.subTest(suffix=suffix):
                self.setUp()
                self.setup_source(content, suffix)
                parts = [self.part(f"{i}.json", [entry]) for i, entry in
                         enumerate(self.document["translations"])]
                merged = self.root / "merged.json"
                self.assertEqual(guard.merge(self.source, merged, parts), 2)
                guard.render(self.source, merged, self.target)
                self.assertEqual(self.source.read_bytes(), self.target.read_bytes())
                with self.assertRaises(FileExistsError):
                    guard.merge(self.source, merged, parts)

    def test_merge_rejects_missing_duplicate_reordered_and_empty(self):
        self.setup_source()
        a = self.part("a.json", self.document["translations"][:1])
        b = self.part("b.json", self.document["translations"][1:])
        empty = self.part("empty.json", [])
        for parts in [[a], [a, a], [b, a], [a, b, b], [a, empty, b], []]:
            with self.subTest(parts=parts), self.assertRaises(guard.GuardError):
                guard.merge(self.source, self.root / "merged.json", parts)
            self.assertFalse((self.root / "merged.json").exists())

    def test_cli_pipeline(self):
        self.setup_source()
        a = self.part("a.json", self.document["translations"][:1])
        b = self.part("b.json", self.document["translations"][1:])
        for args in [
            ["batch", self.source, self.root / "batch.json", "--count", "1"],
            ["check", self.source, a, "--count", "1"],
            ["merge", self.source, self.root / "merged.json", a, b],
            ["render", self.source, self.root / "merged.json", self.target],
            ["verify", self.source, self.target],
        ]:
            result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([sys.executable, str(SCRIPT), "batch", str(self.source),
                                 str(self.root / "bad.json"), "--start", "0"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR:", result.stderr)


if __name__ == "__main__":
    unittest.main()
