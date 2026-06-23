# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

from scidownl.api.cli import read_keywords_from_file


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


if __name__ == '__main__':
    unittest.main()
