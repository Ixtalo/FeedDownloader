"""Unit tests."""

import zipfile
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

import downloader

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>a</title><link>https://x.test/a/story.html</link></item>
<item><title>b</title><link>https://x.test/b/story.html</link></item>
<item><title>c</title><link>https://x.test/c/none.html</link></item>
</channel></rss>"""


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path.endswith("feed.xml"):
        return httpx.Response(200, text=RSS)
    if path.startswith("/a/"):
        return httpx.Response(200, text="<html><article>A</article></html>")
    if path.startswith("/b/"):
        return httpx.Response(404)
    return httpx.Response(200, text="<html><p>no article</p></html>")


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


class TestGetFilenameFromUrl:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("", ""),
            ("foo", "foo"),
            ("https://foo/bar/xy.rss2", "xy.rss2"),
            ("https://foo/bar//xy.rss2", "xy.rss2"),
            ("https://foo/bar/", "bar"),
        ],
    )
    def test_names(self, url: str, expected: str) -> None:
        assert downloader.get_filename_from_url(url) == expected


class TestUniqueName:
    def test_collisions(self) -> None:
        used: set[str] = set()
        assert downloader.unique_name("a.html", used) == "a.html"
        assert downloader.unique_name("a.html", used) == "a-2.html"
        assert downloader.unique_name("a.html", used) == "a-3.html"
        assert downloader.unique_name("x", used) == "x"
        assert downloader.unique_name("x", used) == "x-2"


class TestExtractArticle:
    def test_found(self) -> None:
        assert downloader.extract_article("<html><article>A</article></html>") == "<article>A</article>"

    def test_missing(self) -> None:
        assert downloader.extract_article("<html><p>x</p></html>") is None


class TestDownload:
    def test_stores_feed_and_articles(self, client: httpx.Client, tmp_path: Path) -> None:
        target = tmp_path / "out.zip"
        stored = downloader.download(client, "https://x.test/feed.xml", target)
        assert stored == 1  # b -> 404, c -> no <article>
        with zipfile.ZipFile(target) as zf:
            assert sorted(zf.namelist()) == ["feed.xml.xml", "story.html.html"]
            assert zf.read("story.html.html") == b"<article>A</article>"

    def test_limit(self, client: httpx.Client, tmp_path: Path) -> None:
        stored = downloader.download(client, "https://x.test/feed.xml", tmp_path / "o.zip", limit=1)
        assert stored == 1

    def test_http_error(self, client: httpx.Client, tmp_path: Path) -> None:
        with pytest.raises(httpx.HTTPStatusError):
            downloader.download(client, "https://x.test/b/feed", tmp_path / "o.zip")

    def test_existing_zip_not_overwritten(self, client: httpx.Client, tmp_path: Path) -> None:
        target = tmp_path / "o.zip"
        target.write_bytes(b"")
        with pytest.raises(FileExistsError):
            downloader.download(client, "https://x.test/feed.xml", target)


class TestCli:
    def test_invalid_url(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(downloader.app, ["not-a-url", str(tmp_path)])
        assert result.exit_code != 0

    def test_run(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(downloader, "make_client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
        result = CliRunner().invoke(downloader.app, ["https://x.test/feed.xml", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert len(list(tmp_path.glob("*.zip"))) == 1
