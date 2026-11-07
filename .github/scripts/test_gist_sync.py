import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import gist_sync
from gist_client import GitHubGistClient


GIST_ID = "a" * 32


class GistSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.asset_root = self.root / "gamedev" / "nanoswarm"
        self.asset_root.mkdir(parents=True)
        self.devlog_dir = self.asset_root / "Devlog_10"
        self.devlog_dir.mkdir()
        (self.asset_root / "Devlog#10 - Beginning to create the Tutorial.md").write_text(
            "# Devlog", encoding="utf-8"
        )
        self.client = Mock()

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_code(self, filename="movement.gd", content="extends Node\n"):
        (self.devlog_dir / filename).write_text(content, encoding="utf-8")

    def add_metadata(self, description="Devlog#10 - Beginning to create the Tutorial"):
        gist_sync.write_metadata(self.devlog_dir / "gist.yml", {
            "id": GIST_ID,
            "url": f"https://gist.github.com/{GIST_ID}",
            "description": description,
        })

    def test_discovery_is_numeric_and_only_matches_devlog_directories(self):
        (self.asset_root / "Devlog_2").mkdir()
        (self.asset_root / "Devlog_misc").mkdir()

        found = gist_sync.discover_devlog_dirs(self.root)

        self.assertEqual([number for number, _ in found], [2, 10])

    def test_create_gist_and_write_metadata(self):
        self.add_code()
        self.client.create_gist.return_value = {
            "id": GIST_ID,
            "html_url": f"https://gist.github.com/{GIST_ID}",
        }

        result = gist_sync.sync_all(self.root, self.client)

        self.assertEqual(result["created"], 1)
        self.client.create_gist.assert_called_once_with(
            "Devlog#10 - Beginning to create the Tutorial",
            {"movement.gd": "extends Node\n"},
            public=False,
        )
        metadata = gist_sync.load_metadata(self.devlog_dir / "gist.yml")
        self.assertEqual(metadata["id"], GIST_ID)

    def test_empty_devlog_does_not_create_or_delete_gist(self):
        result = gist_sync.sync_all(self.root, self.client)

        self.assertEqual(result["skipped"], 1)
        self.client.create_gist.assert_not_called()
        self.client.get_gist.assert_not_called()
        self.client.delete_gist.assert_not_called()

    def test_sync_updates_added_edited_and_deleted_files_and_description(self):
        self.add_code("changed.gd", "new content")
        self.add_code("added.gd", "added content")
        self.add_metadata(description="Old description")
        self.client.get_gist.return_value = {
            "description": "Old description",
            "files": {
                "changed.gd": {"content": "old content"},
                "removed.gd": {"content": "removed content"},
            },
        }

        result = gist_sync.sync_all(self.root, self.client)

        self.assertEqual(result["updated"], 1)
        self.client.update_gist.assert_called_once_with(
            GIST_ID,
            add_files={"added.gd": "added content"},
            edit_files={"changed.gd": "new content"},
            delete_files=["removed.gd"],
            description="Devlog#10 - Beginning to create the Tutorial",
        )
        self.assertEqual(
            gist_sync.load_metadata(self.devlog_dir / "gist.yml")["description"],
            "Devlog#10 - Beginning to create the Tutorial",
        )

    def test_unchanged_files_skip_update(self):
        self.add_code(content="same content")
        self.add_metadata()
        self.client.get_gist.return_value = {
            "description": "Devlog#10 - Beginning to create the Tutorial",
            "files": {"movement.gd": {"content": "same content"}},
        }

        result = gist_sync.sync_all(self.root, self.client)

        self.assertEqual(result["unchanged"], 1)
        self.client.update_gist.assert_not_called()

    def test_metadata_description_refreshes_without_api_update(self):
        self.add_code(content="same content")
        self.add_metadata(description="Old description")
        self.client.get_gist.return_value = {
            "description": "Devlog#10 - Beginning to create the Tutorial",
            "files": {"movement.gd": {"content": "same content"}},
        }

        gist_sync.sync_all(self.root, self.client)

        self.client.update_gist.assert_not_called()
        self.assertEqual(
            gist_sync.load_metadata(self.devlog_dir / "gist.yml")["description"],
            "Devlog#10 - Beginning to create the Tutorial",
        )

    def test_invalid_gist_id_stops_without_creating_replacement(self):
        self.add_code()
        gist_sync.write_metadata(self.devlog_dir / "gist.yml", {
            "id": "invalid",
            "url": "https://gist.github.com/invalid",
            "description": "Existing",
        })

        with self.assertRaisesRegex(gist_sync.GistSyncError, "Invalid Gist ID"):
            gist_sync.sync_all(self.root, self.client)

        self.client.create_gist.assert_not_called()
        self.client.get_gist.assert_not_called()

    def test_incomplete_remote_file_stops_without_update(self):
        self.add_code()
        self.add_metadata()
        self.client.get_gist.return_value = {
            "description": "Devlog#10 - Beginning to create the Tutorial",
            "files": {"movement.gd": {"truncated": True}},
        }

        with self.assertRaisesRegex(gist_sync.GistSyncError, "incomplete content"):
            gist_sync.sync_all(self.root, self.client)

        self.client.update_gist.assert_not_called()

    def test_only_top_level_gd_files_are_included(self):
        self.add_code()
        nested_dir = self.devlog_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested.gd").write_text("ignored", encoding="utf-8")
        (self.devlog_dir / "other.cs").write_text("ignored", encoding="utf-8")
        self.client.create_gist.return_value = {
            "id": GIST_ID,
            "html_url": f"https://gist.github.com/{GIST_ID}",
        }

        gist_sync.sync_all(self.root, self.client)

        self.assertEqual(
            self.client.create_gist.call_args.args[1],
            {"movement.gd": "extends Node\n"},
        )

    def test_client_sends_description_only_update(self):
        client = GitHubGistClient(token="test-token")
        client._request = Mock(return_value={})

        client.update_gist(GIST_ID, description="Updated title")

        client._request.assert_called_once_with(
            "PATCH",
            f"/{GIST_ID}",
            {"files": {}, "description": "Updated title"},
        )


if __name__ == "__main__":
    unittest.main()