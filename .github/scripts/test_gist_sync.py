import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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

    def test_changed_paths_uses_full_range_and_disables_rename_detection(self):
        result = Mock(stdout=b"gamedev/nanoswarm/Devlog_10/movement.gd\0")
        with patch("gist_sync.subprocess.run", return_value=result) as run:
            paths = gist_sync.get_changed_paths(self.root, "a" * 40, "b" * 40)

        self.assertEqual(paths, ["gamedev/nanoswarm/Devlog_10/movement.gd"])
        self.assertEqual(run.call_args.args[0][1:5], [
            "diff", "--no-renames", "--name-only", "-z",
        ])
        self.assertEqual(run.call_args.args[0][5:7], ["a" * 40, "b" * 40])

    def test_changed_path_selection_includes_top_level_code_and_existing_markdown(self):
        nested_dir = self.devlog_dir / "nested"
        nested_dir.mkdir()
        (nested_dir / "nested.gd").write_text("ignored", encoding="utf-8")
        changed_paths = [
            "gamedev/nanoswarm/Devlog_10/movement.gd",
            "gamedev/nanoswarm/Devlog_10/nested/nested.gd",
            "gamedev/nanoswarm/Devlog#10 - Beginning to create the Tutorial.md",
            "gamedev/nanoswarm/Devlog#11 - Deleted post.md",
            "gamedev/nanoswarm/Devlog_10/gist.yml",
            "gamedev/nanoswarm/Devlog#10 - unrelated.txt",
        ]

        affected = gist_sync.affected_devlog_numbers(changed_paths, self.root)

        self.assertEqual(affected, [10])

    def test_markdown_only_change_selects_its_devlog(self):
        affected = gist_sync.affected_devlog_numbers(
            ["gamedev/nanoswarm/Devlog#10 - Beginning to create the Tutorial.md"],
            self.root,
        )

        self.assertEqual(affected, [10])

    def test_update_sync_only_processes_affected_devlog(self):
        self.add_code()
        other_dir = self.asset_root / "Devlog_2"
        other_dir.mkdir()
        (other_dir / "other.gd").write_text("other", encoding="utf-8")
        (self.asset_root / "Devlog#2 - Other post.md").write_text(
            "# Other", encoding="utf-8"
        )
        self.client.create_gist.return_value = {
            "id": GIST_ID,
            "html_url": f"https://gist.github.com/{GIST_ID}",
        }

        with patch.object(
            gist_sync,
            "get_changed_paths",
            return_value=["gamedev/nanoswarm/Devlog_10/movement.gd"],
        ):
            result = gist_sync.sync_update(self.root, "a" * 40, "b" * 40, self.client)

        self.assertEqual(result["created"], 1)
        self.client.create_gist.assert_called_once_with(
            "Devlog#10 - Beginning to create the Tutorial",
            {"movement.gd": "extends Node\n"},
            public=False,
        )

    def test_update_sync_falls_back_to_full_when_range_is_unavailable(self):
        expected = {"created": 0, "updated": 1, "unchanged": 0, "skipped": 0}
        with patch.object(
            gist_sync,
            "get_changed_paths",
            side_effect=gist_sync.GistSyncError("missing range"),
        ), patch.object(gist_sync, "sync_all", return_value=expected) as sync_all:
            result = gist_sync.sync_update(self.root, None, "b" * 40, self.client)

        self.assertEqual(result, expected)
        sync_all.assert_called_once_with(self.root, self.client)

    def test_update_sync_skips_unrelated_changes_without_constructing_client(self):
        with patch.object(
            gist_sync,
            "get_changed_paths",
            return_value=["gamedev/nanoswarm/Devlog_99/gist.yml"],
        ), patch.object(gist_sync, "GitHubGistClient") as client_class:
            result = gist_sync.sync_update(self.root, "a" * 40, "b" * 40)

        self.assertEqual(result, {"created": 0, "updated": 0, "unchanged": 0, "skipped": 0})
        client_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()