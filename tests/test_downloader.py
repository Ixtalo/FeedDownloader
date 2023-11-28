#!pytest
# -*- coding: utf-8 -*-
"""Unit tests."""

# pylint: disable=missing-function-docstring, line-too-long, invalid-name

import pytest
from feeddownloader.downloader import __get_just_filename_from_url


def test_get_just_filename_from_url():
    with pytest.raises(AssertionError):
        __get_just_filename_from_url(None)
    assert __get_just_filename_from_url("") == ""
    assert __get_just_filename_from_url("foo") == "foo"
    assert __get_just_filename_from_url("https://foo/bar/xy.rss2") == "xy.rss2"
    assert __get_just_filename_from_url("https://foo/bar//xy.rss2") == "xy.rss2"
