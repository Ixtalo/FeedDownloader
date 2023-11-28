# (RSS) Feed Downloader

Download feeds (e.g. RSS) and all linked pages, like a crawler/scraper,
and store the collected RSS articles into ZIP files.

Only the RSS `<article>` parts are stored.

## Requirements

* Python 3.10+
* Poetry (install with `python3 -m pip install -U --user poetry`)

## Usage

1. `poetry install --only=main` (once)
2. `poetry run python feeddownloader/downloader.py <RSS-URL> <OUTPUT-FOLDER>`


Example:
`poetry run python feeddownloader/downloader.py "https://www.tagesschau.de/index~rss2.xml" output/`
