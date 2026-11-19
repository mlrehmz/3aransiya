import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class SentenceSplitTest(unittest.TestCase):
    def test_groups_variants_and_preserves_existing_output_on_bad_checksum(self):
        fixture = """darija,darija_ar
salam 3likom,سلام عليكم
salam 3likom!,سلام عليكم
salam 3likum,سلام عليكم
salam 3likum,سلام عاليكم
hna,هنا
!,؟
"""
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            manifest = Path(directory) / "manifest.json"
            source.write_bytes(fixture.encode("utf-8"))
            checksum = hashlib.sha256(source.read_bytes()).hexdigest()
            command = [
                sys.executable, "-m", "project_tools.sentence_split", str(source), str(manifest),
                "--sha256",
            ]
            subprocess.run([*command, checksum], check=True, capture_output=True)
            original = manifest.read_bytes()
            result = json.loads(original)
            assignments = result["assignments"]
            self.assertEqual([row["record"] for row in assignments], [1, 2, 3, 4, 5])
            self.assertEqual([row["group"] for row in assignments], [1, 1, 1, 1, 5])
            self.assertEqual(len({row["split"] for row in assignments[:4]}), 1)
            self.assertEqual(result["rejected"], [{"record": 6, "reason": "empty key"}])
            subprocess.run([*command, checksum], check=True, capture_output=True)
            self.assertEqual(manifest.read_bytes(), original)
            failure = subprocess.run([*command, "0" * 64], capture_output=True, text=True)
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn("checksum", failure.stderr)
            self.assertEqual(manifest.read_bytes(), original)

    def test_v2_groups_case_variants_with_different_arabic_keys(self):
        fixture = "darija,darija_ar\nayeh!,أيه!\nAyeh.,آيه.\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            manifest = Path(directory) / "manifest.json"
            data = fixture.encode("utf-8")
            source.write_bytes(data)
            subprocess.run([
                sys.executable, "-m", "project_tools.sentence_split", str(source), str(manifest),
                "--sha256", hashlib.sha256(data).hexdigest(), "--rule", "v2",
            ], check=True)
            result = json.loads(manifest.read_bytes())
            self.assertEqual(result["rule"], "doda-sentence-split-v2")
            self.assertEqual([row["group"] for row in result["assignments"]], [1, 1])
            self.assertEqual(result["overlapping_keys"]["lowercase_latin"], 0)
