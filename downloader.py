#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""downloader.py - Feed (e.g. RSS) downloader.

Download feeds (e.g. RSS) and all linked pages, like a crawler/scraper.

Usage:
  downloader.py [options] <url> <output-folder>
  downloader.py -h | --help
  downloader.py --version

Arguments:
  url               Feed URL.
  output-folder     Output directory, must be absolute path!

Options:
  -h --help         Show this screen.
  --logfile=FILE    Logging to FILE, otherwise use STDOUT.
  --no-color        No colored log output.
  -v --verbose      Be more verbose.
  --version         Show version.
"""
##
# LICENSE:
##
# Copyright (C) 2020-2022 Ixtalo, ixtalo@gmail.com
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
##
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
import os
import sys
import time
import zipfile
import os.path
import logging
from pathlib import Path
from urllib.parse import urlparse
import feedparser   # https://pythonhosted.org/feedparser/
import requests
import colorlog
import validators
from docopt import docopt
from bs4 import BeautifulSoup

__version__ = "1.3.1"
__date__ = "2020-05-12"
__updated__ = "2022-10-07"
__author__ = "Ixtalo"
__license__ = "AGPL-3.0+"
__email__ = "ixtalo@gmail.com"
__status__ = "Production"


HTTP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/105.0"
LOGGING_STREAM = sys.stdout
DEBUG = bool(os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"))
__script_dir = Path(__file__).parent


# check for Python3
if sys.version_info < (3, 0):
    sys.stderr.write("Minimum required version is Python 3.x!\n")
    sys.exit(1)


def __setup_logging(log_file: str = None, verbose=False, no_color=False):
    if log_file:
        stream = open(log_file, "a", encoding="utf8")
        no_color = True
    else:
        stream = LOGGING_STREAM
    handler = colorlog.StreamHandler(stream=stream)

    format_string = "%(log_color)s%(asctime)s %(levelname)-8s %(message)s"
    formatter = colorlog.ColoredFormatter(format_string, datefmt="%Y-%m-%d %H:%M:%S", no_color=no_color)
    handler.setFormatter(formatter)

    logging.basicConfig(level=logging.WARNING, handlers=[handler])
    if verbose or log_file:
        logging.getLogger("").setLevel(logging.INFO)
    if DEBUG:
        logging.getLogger("").setLevel(logging.DEBUG)


def __http_get(url):
    headers = {
        "User-Agent": HTTP_USER_AGENT
    }
    response = requests.get(url, headers=headers, timeout=60)
    logging.debug("HTTP GET result: %s", response)
    return response


def __get_url_just_filename(url: str):
    """Extract just the filename of a URL, e.g., 'index.html'."""
    assert url is not None
    return os.path.basename(urlparse(url).path)


def run(feed_url: str, output_dir: Path):
    """Run the main job.

    :param feed_url: URL string
    :param output_dir: target output directory
    :return: result code
    """
    assert isinstance(output_dir, Path)
    assert output_dir.exists() and output_dir.is_dir()
    assert validators.url(feed_url), "Invalid URL!"

    # construct output filename, e.g. '2020-05-12_125241.zip'
    now = time.strftime("%Y-%m-%d_%H%M%S")
    zip_filepath = output_dir.joinpath(f"{now}.zip")
    logging.info("output ZIP: %s", zip_filepath.resolve())
    assert not zip_filepath.exists(), "Output file must not exist!"

    # HTP GET
    # RSS is basically XML
    response = __http_get(feed_url)
    assert response and response.ok, "No data for URL!"

    # HTTP feed parser
    feed = feedparser.parse(response.text,
                            agent=HTTP_USER_AGENT,
                            referrer=feed_url)
    assert feed and feed.entries, "No feed data!"

    with zipfile.ZipFile(zip_filepath, "a", zipfile.ZIP_DEFLATED) as zf:
        basename = __get_url_just_filename(feed_url)
        zf.writestr(f"{basename}.xml", response.text)

        # process linked feed entries
        for i, entry in enumerate(feed.entries):
            try:
                logging.info("Processing %d/%d: %s", i + 1, len(feed.entries), entry.link)
                response = __http_get(entry.link)
                if response:
                    # extract only the feed story
                    soup = BeautifulSoup(response.text, 'lxml')
                    story = soup.select('article.story')
                    if story:
                        article = str(story[0])
                        entry_basename = __get_url_just_filename(entry.link)
                        zf.writestr("%s.html" % entry_basename, article)
                    else:
                        logging.warning("No element article.story for %s", entry.link)
                else:
                    logging.warning("No result for %s", entry.link)
            except Exception as ex:
                logging.exception(ex)

    return 0


def main():
    """Run main program entry.

    :return: exit/return code
    """
    version_string = f"Feed Downloader {__version__} ({__updated__})"
    arguments = docopt(__doc__, version=version_string)
    arg_feed_url = arguments['<url>']
    arg_output_dir = arguments['<output-folder>']
    arg_logfile = arguments["--logfile"]
    arg_nocolor = arguments["--no-color"]
    arg_verbose = arguments["--verbose"]

    __setup_logging(arg_logfile, arg_verbose, arg_nocolor)
    logging.info(version_string)

    output_dir = Path(arg_output_dir)
    if not output_dir.exists():
        # try output directory inside script's folder
        output_dir = __script_dir.joinpath(output_dir)
        if not output_dir.exists():
            # still no valid output directory...
            raise NotADirectoryError("Output directory does not exist!")
    logging.info("output_dir: %s", output_dir.resolve())

    return run(arg_feed_url, output_dir)


if __name__ == '__main__':
    if DEBUG:
        # sys.argv.append('--verbose')
        pass
    if os.environ.get("PROFILE", "").lower() in ("true", "1", "yes"):
        import cProfile
        import pstats
        profile_filename = f"{__file__}.profile"
        cProfile.run('main()', profile_filename)
        with open(f'{profile_filename}.txt', 'w', encoding="utf8") as statsfp:
            profile_stats = pstats.Stats(profile_filename, stream=statsfp)
            stats = profile_stats.strip_dirs().sort_stats('cumulative')
            stats.print_stats()
        sys.exit(0)
    sys.exit(main())
