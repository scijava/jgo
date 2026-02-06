"""jgo search - Search for artifacts in Maven repositories"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from datetime import datetime
from typing import TYPE_CHECKING

import rich_click as click

from ...config import GlobalSettings
from ...parse.coordinate import Coordinate
from ...styles import (
    COORD_HELP_FULL,
    COORD_HELP_SHORT,
    MAVEN_REPOSITORIES,
    secondary,
    syntax,
    tip,
)
from ...util.logging import log_exception_if_verbose
from ..args import build_parsed_args
from ..console import console_print
from ..output import print_dry_run
from ..rich.formatters import format_coordinate

if TYPE_CHECKING:
    from ..args import ParsedArgs

_log = logging.getLogger(__name__)


@click.command(
    help=f"Search for artifacts in {MAVEN_REPOSITORIES}. "
    f"Supports plain text, coordinates ({COORD_HELP_SHORT}), or SOLR syntax ({syntax('g: a:')}).",
    epilog=tip(
        f"Try {syntax('g:groupId a:artifactId')} for SOLR syntax, "
        f"{COORD_HELP_FULL} for coordinates, or plain text. "
        f"Use {syntax('*')} for wildcards and {syntax('~')} for fuzzy search."
    ),
)
@click.option(
    "--limit",
    type=int,
    default=20,
    metavar="N",
    help=f"Limit number of results {secondary('(default: 20)')}",
)
@click.option(
    "--repository",
    metavar="NAME",
    help=f"Search specific repository {secondary('(default: central)')}",
)
@click.option(
    "--detailed",
    is_flag=True,
    help="Show detailed metadata for each result",
)
@click.argument(
    "query",
    nargs=-1,
    required=True,
    cls=click.RichArgument,
    help=f"Search terms. Supports plain text, coordinates ({COORD_HELP_SHORT}), or SOLR syntax (g: a:)",
)
@click.pass_context
def search(ctx, limit, repository, detailed, query):
    """
    Search for artifacts in Maven repositories.

    The QUERY argument supports three input styles:

    1. **Plain Text** - Searches across all fields (groupId, artifactId, description):
       - jgo search apache commons
       - jgo search junit

    2. **Maven Coordinates** - Automatically converted to SOLR query:
       - jgo search org.apache.commons:commons-lang3
       - jgo search junit:junit:4.13.2

    3. **SOLR Field Syntax** - Direct field queries with advanced features:
       - jgo search g:org.apache.commons a:commons-lang3
       - jgo search a:jackson-databind v:2.15*
       - jgo search a:jacksn~ (fuzzy search)

    SOLR Field Names:
      - g:groupId - Search by group ID
      - a:artifactId - Search by artifact ID
      - v:version - Search by version
      - p:packaging - Search by packaging type (jar, pom, etc.)
      - c:classifier - Search by classifier

    Advanced SOLR Features (work with field syntax only):
      - Wildcards: Use * for multiple characters, ? for single character
        Example: jgo search a:jackson-*
      - Fuzzy Search: Use ~ for typo tolerance (edit distance 0-2)
        Example: jgo search a:jacksn~ (finds "jackson")
        Example: jgo search a:scijav~1 (edit distance 1)

    Args:
        query: One or more search terms
        limit: Maximum number of results to return (default: 20)
        repository: Repository to search (currently only 'central' supported)
        detailed: Show additional metadata (version count, packaging, last updated)
    """

    opts = ctx.obj
    config = GlobalSettings.load_from_opts(opts)
    args = build_parsed_args(opts, command="search")

    # Join query parts into a single string
    query_str = " ".join(query)

    exit_code = execute(
        args,
        config.to_dict(),
        query=query_str,
        limit=limit,
        repository=repository,
        detailed=detailed,
    )
    ctx.exit(exit_code)


def execute(
    args: ParsedArgs,
    config: dict,
    query: str,
    limit: int = 20,
    repository: str | None = None,
    detailed: bool = False,
) -> int:
    """
    Execute the search command.

    Args:
        args: Parsed command line arguments
        config: Global settings
        query: Search query
        limit: Maximum number of results to show
        repository: Specific repository to search (currently only 'central' supported)
        detailed: Show detailed metadata for each result

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if not query:
        _log.error("Search query is required")
        return 1

    # For now, only support Maven Central
    # Future enhancement: support custom repositories
    if repository and repository != "central":
        console_print(
            f"Error: Repository '{repository}' is not supported. Only 'central' is currently supported.",
            stderr=True,
        )
        return 1

    _log.info(f"Searching Maven Central for: {query}")

    # Dry run
    if args.dry_run:
        print_dry_run(f"Would search Maven Central for '{query}' with limit {limit}")
        return 0

    # Search Maven Central
    try:
        results = _search_maven_central(query, limit)

        if not results:
            console_print(f"No artifacts found for query: {query}")
            return 0

        # Display results
        _display_results(results, detailed=detailed)

        return 0

    except Exception as e:
        _log.error(f"Failed to search Maven Central: {e}")
        log_exception_if_verbose(args.verbose)
        return 1


def _convert_query_to_solr(query: str) -> str:
    """
    Convert a query to SOLR syntax if needed.

    Handles three cases:
    1. Already SOLR syntax (has field prefixes like g:, a:, v:) → pass through
    2. Maven coordinate format (G:A or G:A:V) → convert to SOLR AND query
    3. Plain text → pass through for default SOLR full-text search

    Args:
        query: The search query string

    Returns:
        SOLR-formatted query string
    """
    # Check if already SOLR syntax (field prefixes)
    # Common SOLR fields: g, a, v, p, c, l, ec, fc
    if re.search(r"\b(g|a|v|p|c|l|ec|fc):", query):
        _log.debug(f"Query already in SOLR syntax: {query}")
        return query

    # Try parsing as Maven coordinate (contains : but not SOLR syntax)
    if ":" in query:
        try:
            coord = Coordinate.parse(query)
            parts = [f"g:{coord.groupId}", f"a:{coord.artifactId}"]
            if coord.version:
                parts.append(f"v:{coord.version}")
            if coord.packaging:
                parts.append(f"p:{coord.packaging}")
            if coord.classifier:
                parts.append(f"c:{coord.classifier}")
            solr_query = " AND ".join(parts)
            _log.debug(f"Converted coordinate '{query}' to SOLR: {solr_query}")
            return solr_query
        except ValueError:
            # Not a valid coordinate, treat as plain text
            _log.debug(f"Failed to parse as coordinate, using as plain text: {query}")
            pass

    # Plain text - pass through
    _log.debug(f"Using plain text query: {query}")
    return query


def _search_maven_central(query: str, limit: int) -> list[dict]:
    """
    Search Maven Central using the SOLR API.

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        List of artifact dictionaries
    """
    # Convert query to SOLR syntax if needed
    solr_query = _convert_query_to_solr(query)

    # Build query URL
    base_url = "https://search.maven.org/solrsearch/select"
    params = {
        "q": solr_query,
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
        # Extract description from text array (if available)
        # The text array contains various searchable text, so we need to be selective
        description = ""
        if "text" in doc and isinstance(doc["text"], list):
            # Look for text that looks like actual description (not coordinates, filenames, etc.)
            for text in doc["text"]:
                if not text:
                    continue
                # Skip if it looks like a coordinate, filename, or single word
                if (
                    ":" in text
                    or "." in text[-5:]  # likely a file extension
                    or len(text.split()) < 2  # single word, probably not a description
                    or text.startswith("-")  # likely a classifier or flag
                ):
                    continue
                # Found something that might be a description
                description = text
                break

        result = {
            "group_id": doc.get("g", ""),
            "artifact_id": doc.get("a", ""),
            "latest_version": doc.get("latestVersion", ""),
            "version_count": doc.get("versionCount", 0),
            "packaging": doc.get("p", "jar"),  # Packaging type (jar, pom, etc.)
            "description": description,
        }

        # Add timestamp if available
        if "timestamp" in doc:
            result["last_updated"] = doc["timestamp"]

        results.append(result)

    return results


def _display_results(results: list[dict], detailed: bool = False) -> None:
    """
    Display search results.

    Args:
        results: List of artifact dictionaries
        detailed: Show detailed metadata for each result
    """
    console_print(f"Found {len(results)} artifacts:")
    console_print()

    for i, result in enumerate(results, 1):
        group_id = result["group_id"]
        artifact_id = result["artifact_id"]
        version = result["latest_version"]

        # Basic format: coordinate and latest version
        coord = Coordinate(group_id, artifact_id, version)
        console_print(f"{i}. {format_coordinate(coord)}")

        # Show description by default (if available)
        description = result.get("description", "")
        if description:
            console_print(f"   {description}")

        # Show additional details in detailed mode
        if detailed:
            version_count = result.get("version_count", 0)
            packaging = result.get("packaging", "")

            if version_count > 1:
                console_print(f"   Available versions: {version_count}")

            if packaging:
                console_print(f"   Packaging: {packaging}")

            if "last_updated" in result:
                # Convert timestamp to readable format
                timestamp = result["last_updated"]
                # Timestamp is in milliseconds
                dt = datetime.fromtimestamp(timestamp / 1000)
                console_print(f"   Last updated: {dt.strftime('%Y-%m-%d')}")

        console_print()
