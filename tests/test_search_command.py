#!/usr/bin/env python3
"""
Unit tests for search CLI command.
"""

import json
import sys
from unittest.mock import MagicMock, patch

if sys.version_info >= (3, 11):
    pass
else:
    pass


from jgo.cli._args import ParsedArgs
from jgo.cli.commands import _search as search_cmd


def test_search_maven_central_success():
    """Test successful search of Maven Central."""
    # Mock response from Maven Central
    mock_response = {
        "response": {
            "docs": [
                {
                    "g": "junit",
                    "a": "junit",
                    "latestVersion": "4.13.2",
                    "versionCount": 30,
                    "p": "jar",
                    "timestamp": 1614000000000,
                },
                {
                    "g": "org.junit.jupiter",
                    "a": "junit-jupiter",
                    "latestVersion": "5.10.0",
                    "versionCount": 50,
                    "p": "jar",
                    "timestamp": 1630000000000,
                },
            ]
        }
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_response).encode("utf-8")
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        results = search_cmd._search_maven_central("junit", 10)

    assert len(results) == 2
    assert results[0]["group_id"] == "junit"
    assert results[0]["artifact_id"] == "junit"
    assert results[0]["latest_version"] == "4.13.2"
    assert results[1]["group_id"] == "org.junit.jupiter"


def test_search_maven_central_empty_results():
    """Test search with no results."""
    mock_response = {"response": {"docs": []}}

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response_obj = MagicMock()
        mock_response_obj.read.return_value = json.dumps(mock_response).encode("utf-8")
        mock_response_obj.__enter__.return_value = mock_response_obj
        mock_urlopen.return_value = mock_response_obj

        results = search_cmd._search_maven_central("nonexistent", 10)

    assert len(results) == 0


def test_search_execute_success():
    """Test search command execution."""
    args = ParsedArgs(verbose=0, dry_run=False)

    with patch("jgo.cli.commands._search._search_maven_central") as mock_search:
        mock_search.return_value = [
            {
                "group_id": "junit",
                "artifact_id": "junit",
                "latest_version": "4.13.2",
                "version_count": 30,
                "description": "jar",
            }
        ]

        with patch("jgo.cli.commands._search._display_results"):
            exit_code = search_cmd.execute(args, {}, query="junit", limit=10)

    assert exit_code == 0


def test_search_execute_no_query():
    """Test search command with no query."""
    args = ParsedArgs(verbose=0, dry_run=False)

    exit_code = search_cmd.execute(args, {}, query="", limit=10)

    assert exit_code == 1


def test_search_execute_unsupported_repository():
    """Test search command with unsupported repository."""
    args = ParsedArgs(verbose=0, dry_run=False)

    exit_code = search_cmd.execute(
        args, {}, query="junit", limit=10, repository="custom"
    )

    assert exit_code == 1


def test_search_display_results():
    """Test displaying search results."""
    results = [
        {
            "group_id": "junit",
            "artifact_id": "junit",
            "latest_version": "4.13.2",
            "version_count": 30,
            "description": "jar",
            "last_updated": 1614000000000,
        }
    ]

    # Just verify it doesn't crash
    # In real tests, you might want to capture stdout
    search_cmd._display_results(results)


def test_search_dry_run():
    """Test search command in dry run mode."""
    args = ParsedArgs(verbose=0, dry_run=True)

    exit_code = search_cmd.execute(args, {}, query="junit", limit=10)

    assert exit_code == 0
