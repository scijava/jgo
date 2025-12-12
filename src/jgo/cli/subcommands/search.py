"""jgo search - Search for artifacts in Maven repositories"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs


def execute(
    args: ParsedArgs,
    config: dict,
    query: str,
    limit: int = 20,
    repository: str | None = None,
) -> int:
    """
    Execute the search command.

    Args:
        args: Parsed command line arguments
        config: Configuration from ~/.jgorc
        query: Search query
        limit: Maximum number of results to show
        repository: Specific repository to search (currently only 'central' supported)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if not query:
        print("Error: Search query is required", file=sys.stderr)
        return 1

    # For now, only support Maven Central
    # Future enhancement: support custom repositories
    if repository and repository != "central":
        print(
            f"Error: Repository '{repository}' is not supported. Only 'central' is currently supported.",
            file=sys.stderr,
        )
        return 1

    if args.verbose > 0:
        print(f"Searching Maven Central for: {query}")

    # Dry run
    if args.dry_run:
        print(f"Would search Maven Central for '{query}' with limit {limit}")
        return 0

    # Search Maven Central
    try:
        results = _search_maven_central(query, limit, args.verbose > 1)

        if not results:
            print(f"No artifacts found for query: {query}")
            return 0

        # Display results
        _display_results(results, args.verbose > 0)

        return 0

    except Exception as e:
        print(f"Error: Failed to search Maven Central: {e}", file=sys.stderr)
        if args.verbose > 1:
            import traceback

            traceback.print_exc()
        return 1


def _search_maven_central(query: str, limit: int, debug: bool = False) -> list[dict]:
    """
    Search Maven Central using the SOLR API.

    Args:
        query: Search query
        limit: Maximum number of results
        debug: Whether to print debug info

    Returns:
        List of artifact dictionaries
    """
    # Build query URL
    base_url = "https://search.maven.org/solrsearch/select"
    params = {
        "q": query,
        "rows": str(limit),
        "wt": "json",
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    if debug:
        print(f"Query URL: {url}", file=sys.stderr)

    # Make request
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise Exception(f"Failed to connect to Maven Central: {e}") from e
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse response: {e}") from e

    # Extract results
    if "response" not in data or "docs" not in data["response"]:
        return []

    docs = data["response"]["docs"]

    # Convert to simplified format
    results = []
    for doc in docs:
        result = {
            "group_id": doc.get("g", ""),
            "artifact_id": doc.get("a", ""),
            "latest_version": doc.get("latestVersion", ""),
            "version_count": doc.get("versionCount", 0),
            "description": doc.get("p", ""),  # Packaging type (jar, pom, etc.)
        }

        # Add timestamp if available
        if "timestamp" in doc:
            result["last_updated"] = doc["timestamp"]

        results.append(result)

    return results


def _display_results(results: list[dict], verbose: bool) -> None:
    """
    Display search results.

    Args:
        results: List of artifact dictionaries
        verbose: Whether to show verbose output
    """
    print(f"Found {len(results)} artifacts:")
    print()

    for i, result in enumerate(results, 1):
        group_id = result["group_id"]
        artifact_id = result["artifact_id"]
        version = result["latest_version"]

        # Basic format: coordinate and latest version
        coordinate = f"{group_id}:{artifact_id}"
        print(f"{i}. {coordinate}")
        print(f"   Latest version: {version}")

        if verbose:
            # Show additional details in verbose mode
            version_count = result.get("version_count", 0)
            description = result.get("description", "")

            if version_count > 1:
                print(f"   Available versions: {version_count}")

            if description:
                print(f"   Packaging: {description}")

            if "last_updated" in result:
                # Convert timestamp to readable format
                timestamp = result["last_updated"]
                # Timestamp is in milliseconds
                from datetime import datetime

                dt = datetime.fromtimestamp(timestamp / 1000)
                print(f"   Last updated: {dt.strftime('%Y-%m-%d')}")

        print()
