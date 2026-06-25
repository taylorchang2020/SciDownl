# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from scidownl.api.cli import read_keywords_from_file, read_doi_file


class TestReadKeywordsFromFile(unittest.TestCase):

    def _write_temp_file(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_reads_one_doi_per_line(self):
        path = self._write_temp_file(
            "https://doi.org/10.1145/3375633\n"
            "10.3343/alm.2013.33.1.8\n"
            "10.1002/chin.197335038\n"
        )
        self.assertEqual(read_keywords_from_file(path), [
            "https://doi.org/10.1145/3375633",
            "10.3343/alm.2013.33.1.8",
            "10.1002/chin.197335038",
        ])

    def test_ignores_blank_lines_and_comments_and_strips_whitespace(self):
        path = self._write_temp_file(
            "  https://doi.org/10.1145/3375633  \n"
            "\n"
            "# this is a comment\n"
            "\t10.3343/alm.2013.33.1.8\n"
            "   \n"
        )
        self.assertEqual(read_keywords_from_file(path), [
            "https://doi.org/10.1145/3375633",
            "10.3343/alm.2013.33.1.8",
        ])

    def test_returns_empty_list_for_empty_file(self):
        path = self._write_temp_file("")
        self.assertEqual(read_keywords_from_file(path), [])


class TestReadDoiFile(unittest.TestCase):

    def _write_temp_file(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix='.txt')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path

    def test_plain_doi_lines_have_no_output_path(self):
        path = self._write_temp_file(
            "https://doi.org/10.1145/3375633\n"
            "10.3343/alm.2013.33.1.8\n"
        )
        self.assertEqual(read_doi_file(path), [
            ("https://doi.org/10.1145/3375633", None),
            ("10.3343/alm.2013.33.1.8", None),
        ])

    def test_doi_with_output_path_is_split_on_first_comma(self):
        path = self._write_temp_file(
            "https://doi.org/10.1016/j.measurement.2021.109460,knowledge_base/papers/FD-02.pdf\n"
            "  10.3390/machines10040240 , papers/FD-05.pdf \n"
        )
        self.assertEqual(read_doi_file(path), [
            ("https://doi.org/10.1016/j.measurement.2021.109460", "knowledge_base/papers/FD-02.pdf"),
            ("10.3390/machines10040240", "papers/FD-05.pdf"),
        ])

    def test_trailing_comma_yields_no_output_path(self):
        path = self._write_temp_file("10.3343/alm.2013.33.1.8,\n")
        self.assertEqual(read_doi_file(path), [
            ("10.3343/alm.2013.33.1.8", None),
        ])

    def test_ignores_blank_and_comment_lines(self):
        path = self._write_temp_file(
            "# a manifest\n"
            "\n"
            "10.1145/3375633,papers/a.pdf\n"
        )
        self.assertEqual(read_doi_file(path), [
            ("10.1145/3375633", "papers/a.pdf"),
        ])


if __name__ == '__main__':
    unittest.main()
