
import json
import os
import urllib.error
import urllib.request
from urllib.parse import quote


class GitHubGistError(Exception):
    """Raised when a GitHub Gist API operation fails."""
    pass


class GitHubGistClient:
    API_URL = "https://api.github.com/gists"
    API_VERSION = "2022-11-28"

    def __init__(self, token: str | None = None):
        """
        Initialize the Gist client.

        Token can be supplied directly or through the GIST_TOKEN
        environment variable.
        """
        self.token = token or os.getenv("GIST_TOKEN")

        if not self.token:
            raise ValueError(
                "GitHub token not provided. "
                "Pass a token or set the GIST_TOKEN environment variable."
            )

    def _request(self, method: str, endpoint: str = "", payload: dict | None = None):
        """Perform an authenticated GitHub API request."""

        url = f"{self.API_URL}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
        }

        data = None

        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method=method
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()

                if not body:
                    return None

                return json.loads(body.decode("utf-8"))

        except urllib.error.HTTPError as error:
            try:
                error_body = error.read().decode("utf-8")
                details = json.loads(error_body).get("message", error_body)
            except (ValueError, AttributeError):
                details = error.reason

            raise GitHubGistError(
                f"GitHub API error ({error.code}): {details}"
            ) from error

        except urllib.error.URLError as error:
            raise GitHubGistError(
                f"Could not connect to GitHub: {error.reason}"
            ) from error

    @staticmethod
    def _validate_files(files: dict):
        """Validate a filename-to-content mapping."""

        if not isinstance(files, dict):
            raise ValueError("Files must be a dictionary.")

        for filename, content in files.items():
            if not isinstance(filename, str) or not filename.strip():
                raise ValueError("Filenames must be non-empty strings.")

            if not isinstance(content, str):
                raise ValueError(
                    f"Content for '{filename}' must be a string."
                )

    @staticmethod
    def _format_files(files: dict) -> dict:
        """Convert local files into GitHub API format."""

        return {
            filename: {"content": content}
            for filename, content in files.items()
        }

    def create_gist(
        self,
        description: str,
        files: dict,
        public: bool = False
    ) -> dict:
        """
        Create a new Gist containing multiple files.

        Args:
            description: Gist description.
            files: Dictionary mapping filenames to file contents.
            public: Whether the Gist should be publicly visible.

        Returns:
            GitHub API response containing the new Gist information.
        """

        self._validate_files(files)

        if not files:
            raise ValueError("A Gist must contain at least one file.")

        payload = {
            "description": description,
            "public": public,
            "files": self._format_files(files)
        }

        return self._request("POST", payload=payload)

    def get_gist(self, gist_id: str) -> dict:
        """
        Retrieve an existing Gist, including its file contents.

        Args:
            gist_id: GitHub Gist ID.

        Returns:
            GitHub API response containing Gist information.
        """

        if not gist_id:
            raise ValueError("Gist ID cannot be empty.")

        return self._request(
            "GET",
            f"/{quote(gist_id, safe='')}"
        )

    def update_gist(
        self,
        gist_id: str,
        add_files: dict | None = None,
        edit_files: dict | None = None,
        delete_files: list[str] | None = None,
        description: str | None = None
    ) -> dict:
        """
        Add, edit and/or delete files in an existing Gist.

        Args:
            gist_id: GitHub Gist ID.
            add_files: Files to add.
            edit_files: Existing files to edit.
            delete_files: Filenames to remove.

        Returns:
            GitHub API response containing the updated Gist.
        """

        if not gist_id:
            raise ValueError("Gist ID cannot be empty.")

        add_files = add_files or {}
        edit_files = edit_files or {}
        delete_files = delete_files or []

        self._validate_files(add_files)
        self._validate_files(edit_files)

        if not isinstance(delete_files, list):
            raise ValueError("delete_files must be a list.")

        if any(not isinstance(name, str) or not name.strip()
               for name in delete_files):
            raise ValueError("Deleted filenames must be non-empty strings.")

        # Prevent ambiguous operations on the same filename.
        all_names = (
            set(add_files)
            | set(edit_files)
            | set(delete_files)
        )

        operation_count = (
            len(add_files) + len(edit_files) + len(delete_files)
        )

        if len(all_names) != operation_count:
            raise ValueError(
                "A filename cannot appear in multiple update operations."
            )

        if not all_names and description is None:
            raise ValueError("No update operations provided.")

        # GitHub uses null to indicate file deletion.
        payload = {
            "files": self._format_files(add_files)
        }

        if description is not None:
            if not isinstance(description, str):
                raise ValueError("Description must be a string.")
            payload["description"] = description

        payload["files"].update(self._format_files(edit_files))

        for filename in delete_files:
            payload["files"][filename] = None

        return self._request(
            "PATCH",
            f"/{quote(gist_id, safe='')}",
            payload
        )

    def delete_gist(self, gist_id: str) -> bool:
        """
        Delete an existing Gist.

        Args:
            gist_id: GitHub Gist ID.

        Returns:
            True if GitHub confirms successful deletion.
        """

        if not gist_id:
            raise ValueError("Gist ID cannot be empty.")

        self._request(
            "DELETE",
            f"/{quote(gist_id, safe='')}"
        )

        return True
