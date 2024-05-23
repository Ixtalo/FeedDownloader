# (RSS) Feed Downloader

Download feeds (e.g. RSS) and all linked pages, like a crawler/scraper,
and store the collected RSS articles into ZIP files.

Only the RSS `<article>` parts are stored.

## Requirements

* Python 3.10+
* Poetry (see https://python-poetry.org/docs/#installation)

## Usage

1. set up: `poetry install --only=main --sync` (once)
2. `poetry run python feeddownloader/downloader.py <RSS-URL> <OUTPUT-FOLDER>`


Example:
`poetry run python feeddownloader/downloader.py "https://www.tagesschau.de/index~rss2.xml" output/`
