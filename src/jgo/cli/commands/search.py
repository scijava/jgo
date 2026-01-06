"""jgo search - Search for artifacts in Maven repositories"""

from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING

import rich_click as click

from ...util import is_info_enabled
from ..console import get_console, get_err_console

if TYPE_CHECKING:
    from ..parser import ParsedArgs

_log = logging.getLogger(__name__)
_console = get_console()
_err_console = get_err_console()


@click.command(help="Search for artifacts in [magenta]Maven repositories[/].")
@click.option(
    "--limit",
    type=int,
    default=20,
    metavar="N",
    help="Limit number of results [dim](default: 20)[/]",
)
@click.option(
    "--repository",
    metavar="NAME",
    help="Search specific repository [dim](default: central)[/]",
)
@click.argument("query", nargs=-1, required=True)
@click.pass_context
def search(ctx, limit, repository, query):
    """
    Search for artifacts in Maven repositories.

    The query can be a simple text search or use Maven Central's advanced query syntax.

    EXAMPLES:
      jgo search apache commons          # Search for "apache commons"
      jgo search junit                   # Search for "junit"
      jgo search g:org.apache.commons    # Search by groupId
      jgo search a:commons-lang3         # Search by artifactId
      jgo search --limit 10 jackson      # Limit to 10 results
      jgo search --repository central gson  # Search specific repository

    ADVANCED QUERY SYNTAX:
      g:groupId              Search by group ID
      a:artifactId           Search by artifact ID
      v:version              Search by version
      p:packaging            Search by packaging (jar, pom, etc.)
      c:classifier           Search by classifier

    Multiple terms can be combined:
      jgo search g:org.apache.commons a:commons-lang3
    """
    from ...config import GlobalSettings
    from ..parser import _build_parsed_args

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = _build_parsed_args(opts, command="search")

    # Join query parts into a single string
    query_str = " ".join(query)

    exit_code = execute(
        args,
        config.to_dict(),
        query=query_str,
        limit=limit,
        repository=repository,
    )
    ctx.exit(exit_code)


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
        config: Global settings
        query: Search query
        limit: Maximum number of results to show
        repository: Specific repository to search (currently only 'central' supported)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if not query:
        _log.error("Search query is required")
        return 1

    # For now, only support Maven Central
    # Future enhancement: support custom repositories
    if repository and repository != "central":
        _err_console.print(
            f"Error: Repository '{repository}' is not supported. Only 'central' is currently supported."
        )
        return 1

    _log.info(f"Searching Maven Central for: {query}")

    # Dry run
    if args.dry_run:
        from ..output import print_dry_run

        print_dry_run(f"Would search Maven Central for '{query}' with limit {limit}")
        return 0

    from ...util.logging import log_exception_if_verbose

    # Search Maven Central
    try:
        results = _search_maven_central(query, limit)

        if not results:
            _console.print(f"No artifacts found for query: {query}")
            return 0

        # Display results
        _display_results(results)

        return 0

    except Exception as e:
        _log.error(f"Failed to search Maven Central: {e}")
        log_exception_if_verbose(args.verbose)
        return 1


def _search_maven_central(query: str, limit: int) -> list[dict]:
    """
    Search Maven Central using the SOLR API.

    Args:
        query: Search query
        limit: Maximum number of results

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

    _log.debug(f"Query URL: {url}")

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


def _display_results(results: list[dict]) -> None:
    """
    Display search results.

    Args:
        results: List of artifact dictionaries
    """
    verbose = is_info_enabled()

    _console.print(f"Found {len(results)} artifacts:")
    _console.print()

    for i, result in enumerate(results, 1):
        group_id = result["group_id"]
        artifact_id = result["artifact_id"]
        version = result["latest_version"]

        # Basic format: coordinate and latest version
        from ...parse.coordinate import Coordinate

        coord = Coordinate(group_id, artifact_id, version)
        _console.print(f"{i}. {coord.rich()}")

        if verbose:
            # Show additional details in verbose mode
            version_count = result.get("version_count", 0)
            description = result.get("description", "")

            if version_count > 1:
                _console.print(f"   Available versions: {version_count}")

            if description:
                _console.print(f"   Packaging: {description}")

            if "last_updated" in result:
                # Convert timestamp to readable format
                timestamp = result["last_updated"]
                # Timestamp is in milliseconds
                from datetime import datetime

                dt = datetime.fromtimestamp(timestamp / 1000)
                _console.print(f"   Last updated: {dt.strftime('%Y-%m-%d')}")

        _console.print()
