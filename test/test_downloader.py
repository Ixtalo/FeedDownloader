#!pytest
# -*- coding: utf-8 -*-
"""Unit tests."""

# pylint: disable=missing-function-docstring, line-too-long, invalid-name

import pytest
from downloader import __get_url_just_filename


def test_get_url_just_filename():
    with pytest.raises(AssertionError):
        __get_url_just_filename(None)
    assert __get_url_just_filename("") == ""
    assert __get_url_just_filename("foo") == "foo"
    assert __get_url_just_filename("https://foo/bar/xy.rss2") == "xy.rss2"
    assert __get_url_just_filename("https://foo/bar//xy.rss2") == "xy.rss2"
