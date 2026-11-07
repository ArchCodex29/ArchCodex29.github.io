import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sync_content


GIST_ID = "a" * 32
GIST_USER = "TestUser"


class GistReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.content_dir = self.root / "gamedev" / "nanoswarm"
        self.content_dir.mkdir(parents=True)
        self.source = self.content_dir / "Devlog#99 - Testing the Gist Integration.md"
        self.source.write_text("", encoding="utf-8")
        self.asset_dir = self.content_dir / "Devlog_99"
        self.asset_dir.mkdir()
        self.code_file = self.asset_dir / "my_test_file.gd"
        self.code_file.write_text("extends Node\n", encoding="utf-8")
        self.metadata_path = self.asset_dir / "gist.yml"
        self.metadata_path.write_text(f'id: "{GIST_ID}"\n', encoding="utf-8")
        self.username = patch.dict(os.environ, {"GIST_USERNAME": GIST_USER})
        self.username.start()

    def tearDown(self):
        self.username.stop()
        self.temp_dir.cleanup()

    def rewrite(self, content):
        return sync_content.rewrite_gist_refs(content, self.source, self.root)

    def test_rewrites_local_gd_link_to_gist_shortcode(self):
        result = self.rewrite("[Controller](Devlog_99/my_test_file.gd)")

        self.assertEqual(
            result,
            f'{{{{< gist user="{GIST_USER}" id="{GIST_ID}" '
            'file="my_test_file.gd" >}}',
        )

    def test_rewrites_multiple_references_and_keeps_non_gd_links(self):
        second_file = self.asset_dir / "second.gd"
        second_file.write_text("extends Node\n", encoding="utf-8")
        content = (
            "[One](Devlog_99/my_test_file.gd) "
            "[Two](Devlog_99/second.gd) [Docs](guide.md)"
        )

        result = self.rewrite(content)

        self.assertEqual(result.count("{{< gist "), 2)
        self.assertTrue(result.endswith("[Docs](guide.md)"))

    def test_missing_metadata_leaves_reference_unchanged(self):
        self.metadata_path.unlink()
        content = "[Controller](Devlog_99/my_test_file.gd)"

        with patch("builtins.print") as print_mock:
            result = self.rewrite(content)

        self.assertEqual(result, content)
        self.assertTrue(any("Gist metadata not found" in str(call) for call in print_mock.call_args_list))

    def test_invalid_metadata_id_leaves_reference_unchanged(self):
        self.metadata_path.write_text('id: "not-an-id"\n', encoding="utf-8")
        content = "[Controller](Devlog_99/my_test_file.gd)"

        with patch("builtins.print") as print_mock:
            result = self.rewrite(content)

        self.assertEqual(result, content)
        self.assertTrue(any("invalid Gist ID" in str(call) for call in print_mock.call_args_list))

    def test_rejects_links_to_another_devlog(self):
        other_dir = self.content_dir / "Devlog_10"
        other_dir.mkdir()
        other_file = other_dir / "other.gd"
        other_file.write_text("extends Node\n", encoding="utf-8")
        (other_dir / "gist.yml").write_text(f'id: "{GIST_ID}"\n', encoding="utf-8")
        content = "[Other](Devlog_10/other.gd)"

        with patch("builtins.print") as print_mock:
            result = self.rewrite(content)

        self.assertEqual(result, content)
        self.assertTrue(any("top-level file" in str(call) for call in print_mock.call_args_list))

    def test_rejects_nested_gd_files(self):
        nested_dir = self.asset_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested.gd").write_text("extends Node\n", encoding="utf-8")
        content = "[Nested](Devlog_99/nested/nested.gd)"

        with patch("builtins.print") as print_mock:
            result = self.rewrite(content)

        self.assertEqual(result, content)
        self.assertTrue(any("top-level file" in str(call) for call in print_mock.call_args_list))

    def test_ignores_remote_and_image_links(self):
        content = (
            "[Remote](https://example.com/script.gd) "
            "![Image](Devlog_99/my_test_file.gd)"
        )

        self.assertEqual(self.rewrite(content), content)


if __name__ == "__main__":
    unittest.main()