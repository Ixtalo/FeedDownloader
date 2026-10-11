#!/usr/bin/env python3
"""Feed (e.g. RSS) downloader.

Download feeds (e.g. RSS) and all linked pages, like a crawler/scraper,
and store the collected RSS articles into ZIP files.

Only the RSS `<article>` parts are stored.
"""

import sys
import time
import zipfile
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import feedparser
import httpx
import typer
import validators
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from rich.progress import track

HTTP_TIMEOUT = 60.0
HTTP_RETRIES = 3

app = typer.Typer(add_completion=False, help=__doc__.split("\n\n")[0], rich_markup_mode=None)


def get_filename_from_url(url: str) -> str:
    """Extract just the filename of a URL, e.g., 'index.html'."""
    return Path(urlparse(url).path).name


def unique_name(name: str, used: set[str]) -> str:
    """Return `name`, or `name` with a numeric suffix if it is already in `used`; registers the result."""
    candidate = name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    counter = 1
    while candidate in used:
        counter += 1
        candidate = f"{stem}-{counter}.{ext}" if ext else f"{stem}-{counter}"
    used.add(candidate)
    return candidate


def extract_article(html: str) -> str | None:
    """Return the first `<article>` element of the HTML as string, or None."""
    article = BeautifulSoup(html, "lxml").find("article")
    return str(article) if article else None


def make_client() -> httpx.Client:
    """Create the HTTP client (connection pooling, redirects, connect retries)."""
    return httpx.Client(
        headers={"User-Agent": UserAgent(browsers=["Firefox"]).random},
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        transport=httpx.HTTPTransport(retries=HTTP_RETRIES),
    )


def download(
    client: httpx.Client,
    feed_url: str,
    zip_filepath: Path,
    limit: int | None = None,
) -> int:
    """Download the feed and its linked articles into a new ZIP file.

    :param client: HTTP client
    :param feed_url: feed URL
    :param zip_filepath: target ZIP file (must not exist)
    :param limit: limit the number of linked feed entries (None = all)
    :return: number of stored articles
    """
    response = client.get(feed_url)
    response.raise_for_status()

    feed = feedparser.parse(response.text)
    if not feed.entries:
        msg = f"No feed entries found at '{feed_url}'!"
        raise ValueError(msg)

    entries = feed.entries[:limit]
    stored = 0
    with zipfile.ZipFile(zip_filepath, "x", zipfile.ZIP_DEFLATED) as zf:
        used: set[str] = set()
        # main XML feed overview
        zf.writestr(unique_name(f"{get_filename_from_url(feed_url) or 'feed'}.xml", used), response.text)

        for entry in track(entries, description="Downloading", disable=not sys.stderr.isatty()):
            link = entry.get("link")
            if not link:
                logger.warning("Entry without link, skipping.")
                continue
            try:
                page = client.get(link)
                page.raise_for_status()
            except httpx.HTTPError as ex:
                logger.warning("Download failed for '{}': {}", link, ex)
                continue
            article = extract_article(page.text)
            if article is None:
                logger.error("No <article> element for '{}'! Skipping.", link)
                continue
            zf.writestr(unique_name(f"{get_filename_from_url(link) or 'index'}.html", used), article)
            stored += 1
    return stored


def validate_url(value: str) -> str:
    """Typer callback: ensure a valid URL."""
    if validators.url(value) is not True:
        msg = f"Invalid URL: '{value}'"
        raise typer.BadParameter(msg)
    return value


@app.command()
def main(
    url: Annotated[str, typer.Argument(help="Feed URL.", callback=validate_url)],
    output_folder: Annotated[
        Path,
        typer.Argument(help="Output directory.", exists=True, file_okay=False, writable=True, resolve_path=True),
    ],
    limit: Annotated[
        int | None, typer.Option("--limit", "-n", min=1, help="Limit linked feed entries to the first N articles.")
    ] = None,
) -> None:
    """Download a feed and all linked articles into a timestamped ZIP file."""
    # e.g. '2020-05-12_125241.zip'
    zip_filepath = output_folder / f"{time.strftime('%Y-%m-%d_%H%M%S')}.zip"
    logger.info("Output ZIP: {}", zip_filepath)

    try:
        with make_client() as client:
            stored = download(client, url, zip_filepath, limit)
    except (httpx.HTTPError, ValueError, FileExistsError) as ex:
        logger.error("{}", ex)
        raise typer.Exit(code=1) from ex
    logger.info("Stored {} articles.", stored)


if __name__ == "__main__":
    app()
