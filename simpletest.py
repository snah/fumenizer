#!/usr/bin/env python

import functools

import unittest
import json

import fumenizer


class TestBuildMatrix(unittest.TestCase):
        def compare_image_to_file(self, image_file, data_file):
                matrix = fumenizer.build_matrix(image_file, 20, 0)
                with open(data_file, 'r') as f:
                        expected_matrix = json.load(f)

                self.assertTrue(self.compare_matrices(matrix, expected_matrix))

        def compare_matrices(self, matrix, expected):
                for row in zip(matrix, expected):
                        if sum(x - y for x, y in zip(row[0], row[1])) > 0:
                                return False
                return True

        def test_empty(self):
                self.compare_image_to_file('tetris1.png', 'test/tetris1.json')

        def test_tetris2(self):
                self.compare_image_to_file('tetris2.png', 'test/tetris2.json')

        def test_tetris3(self):
                self.compare_image_to_file('tetris3.png', 'test/tetris3.json')

if __name__ == '__main__':
    unittest.main()
