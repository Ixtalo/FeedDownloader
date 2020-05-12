#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feedownloader.py - Feed (e.g. RSS) downloader

Download feeds (e.g. RSS) and all linked pages, like a crawler/scraper.

Usage:
  feedownloader.py [options] <url> <output-folder>
  feedownloader.py -h | --help
  feedownloader.py --version

Arguments:
  url             Feed URL.
  output-folder   Output directory, must be absolute path!

Options:
  -h --help       Show this screen.
  --version       Show version.
"""
##
## LICENSE:
##
## Copyright (C) 2020 Alexander Streicher
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
import os
import sys
import time
import zipfile
import os.path
import json
import logging
from codecs import open

from docopt import docopt
import feedparser   ## https://pythonhosted.org/feedparser/
import requests
from bs4 import BeautifulSoup

__version__ = "1.0"
__date__ = "2020-05-12"
__updated__ = "2020-05-12"
__author__ = "Ixtalo"
__license__ = "AGPL-3.0+"
__email__ = "ixtalo@gmail.com"
__status__ = "Production"

DEBUG = 0
TESTRUN = 0
PROFILE = 0
__script_dir = os.path.dirname(os.path.realpath(__file__))

## check for Python3
if sys.version_info < (3, 0):
    sys.stderr.write("Minimum required version is Python 3.x!\n")
    sys.exit(1)


def main():
    arguments = docopt(__doc__, version="Feed Downloader %s (%s)"%(__version__, __updated__))
    #print(arguments)

    feed_url = arguments['<url>']
    output_dir = arguments['<output-folder>']

    ## setup logging
    logging.basicConfig(level=logging.INFO if not DEBUG else logging.DEBUG)

    ## make absolute if not already so
    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(os.path.join(__script_dir, output_dir))
    logging.info("Output directory: %s", output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ## Construct output filename, e.g. '2020-05-12_125241.zip'
    now = time.strftime("%Y-%m-%d_%H%M%S")
    zipfilename = os.path.join(output_dir, "%s.zip" % now)
    logging.info("Output store file: %s", zipfilename)

    assert not os.path.exists(zipfilename), "Output file must not exist!"

    ## HTTP feed parser
    feed = feedparser.parse(feed_url)

    with zipfile.ZipFile(zipfilename, "a", zipfile.ZIP_DEFLATED) as zf:
        ## extract just the filename of the URL path
        basename = os.path.basename(requests.utils.urlparse(feed_url).path)
        ## write string as file entry in ZIP
        zf.writestr(basename, json.dumps(feed))

        ## process linked feed entries
        for i, entry in enumerate(feed.entries):
            try:
                logging.info("Processing %d/%d: %s", i, len(feed.entries), entry.link)
                ## HTTP GET
                r = requests.get(entry.link)
                ## extract just the filename of the URL path
                entry_basename = os.path.basename(requests.utils.urlparse(entry.link).path)
                logging.debug("GET result: %s", r)
                if r:
                    ## extract only the feed story
                    soup = BeautifulSoup(r.text, 'lxml')
                    story = soup.select('article.story')
                    if story:
                        article = str(story[0])
                        ## write string as file entry in ZIP
                        zf.writestr("%s.html" % entry_basename, article)
                    else:
                        logging.warning("No element article.story for %s", entry.link)
                else:
                    logging.warning("No result for %s", entry.link)
            except Exception as ex:
                logging.exception(ex)

    return 0


if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
        sys.argv.append("--debug")
        #sys.argv.append("-h")
        pass
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = __file__+'.profile.bin'
        cProfile.run('main()', profile_filename)
        with open("%s.txt" % profile_filename, "wb") as statsfp:
          p = pstats.Stats(profile_filename, stream=statsfp)
          stats = p.strip_dirs().sort_stats('cumulative')
          stats.print_stats()
        sys.exit(0)
    sys.exit(main())
