# (RSS) Feed Downloader

Download feeds (e.g. RSS) and all linked pages, like a crawler/scraper.

## Requirements

* Python 3.10+
* Poetry (install with `python3 -m pip install -U --user poetry`)

## Usage

1. `poetry install --only=main` (once)
2. `poetry run python feeddownloader/downloader.py <RSS-URL> <OUTPUT-FOLDER>`
