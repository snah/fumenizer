#!/usr/bin/env python

import cv2
import numpy as np

try:
    import pyperclip
except ImportError:
    pass

import fumen
import roiselector

import json

import sys
import os
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class PlayfieldConverter:
    """Converts an image of a playfield into a matrix of blocks."""
    def __init__(self, region, threshold, debug=False):
        self.region = region
        self.threshold = threshold
        self.debug = debug

    def build_matrix(self, image):
        """Build a playfield matrix from the given image."""
        playfield = self.region.crop(image)

        matrix = np.zeros((20, 10))
        for row, col, part in self._divide_playfield(playfield):
            matrix[row, col] = self.check_part(part)

        return matrix

    def check_part(self, part):
        """Check if a part contains a block or not."""
        grayscale = cv2.cvtColor(part, cv2.COLOR_BGR2GRAY)
        ret, black_white = cv2.threshold(grayscale, self.threshold, 1, cv2.THRESH_BINARY)

        whites = black_white.sum()
        blacks = black_white.size - whites

        if self.debug:
            cv2.imshow('b', part)
            cv2.imshow('c', grayscale)
            ch = 0xFF & cv2.waitKey()
            if ch == 27:
                raise roiselector.CancelException()

        return self._threshold_function(whites, blacks)

    def _threshold_function(self, whites, blacks):
        return whites > blacks

    def _divide_playfield(self, playfield):
        height, width = playfield.shape[:2]

        block_height = height / 20.
        block_width = width / 10.

        for row in range(20):
            for col in range(10):
                y1 = round(height - (row + 1) * block_height)
                y2 = round(height - row * block_height)
                x1 = round(col * block_width)
                x2 = round((col + 1) * block_width)
                part = playfield[y1:y2, x1:x2]
                yield row, col, part


class TGM1PlayfieldConverter(PlayfieldConverter):
    """Playfiled converter with TGM correction."""
    def build_matrix(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        lower = np.array([0, 150, 85])
        upper = np.array([180, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)

        image = cv2.bitwise_and(image, image, mask=mask)

        # Uncomment for preview of the tgm1 corrected image.
        cv2.imshow('f', region.crop(image))
        cv2.waitKey()

        return super().build_matrix(image)

    def _threshold_function(self, whites, blacks):
        return whites > 60


def export_matrix(matrix, filename):
    with open(filename, 'w') as f:
        json.dump(matrix, f)


def fumenize(matrix, showPreview):
    # Prepare result image
    blank = np.zeros((200, 100, 3), np.uint8)
    frame = fumen.Frame()
    cell = 10

    for row in range(20):
        for col in range(10):
            if matrix[row][col]:
                # Draw gray rectangles where blocks are
                cv2.rectangle(blank, (col * 10 + 2, 190 - row * 10),
                              (col * 10 + 5 + 2, 190 - row * 10 + 5), (105, 105, 105), cv2.FILLED)
            if matrix[19 - row][col]:
                frame.field[cell] = 8
            else:
                frame.field[cell] = 0
            cell += 1

    fumen_url = fumen.make([frame], 0)
    print(fumen_url)
    try:
        pyperclip.copy(fumen_url)
    except NameError:
        pass

    if showPreview:
        # Show result image
        cv2.imshow('d', blank)
        cv2.waitKey()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    # Create default settings file.
    if not os.path.isfile('fumenizer.ini'):
        f = open("fumenizer.ini", "w")
        f.write("[settings]\n")
        f.write("#for TGM a threshold around 20 is recommended\n")
        f.write("threshold=20\n")
        f.write("preview=1\n")
        f.write("tgm1=0\n")
        f.close()

    # Read our config file with a set of defaults.
    config = configparser.ConfigParser()
    config['settings'] = {'threshold': 20,
                          'preview': True,
                          'tgm1': False}
    config.read('fumenizer.ini')

    # Parse our command line arguments. These will take precedence over config file settings.
    argParser = argparse.ArgumentParser(description="Fumenizer Settings")
    argParser.add_argument('imageFile', help='Fumenize this image')
    argParser.add_argument('-t', dest='threshold', action='store',
                           type=float, default=float(config['settings']['threshold']),
                           help='Threshold tolerance')
    argParser.add_argument('-p', dest='preview', action='store_true',
                           help='Show preview')
    argParser.add_argument('-1', dest='tgm1', action='store_true',
                           help='TGM1 Compatibility')
    args = argParser.parse_args()

    # Read image.
    image = cv2.imread(args.imageFile)

    # Let the user select the playfield.
    region_selector = roiselector.ROISelector(image)
    region = region_selector.run()

    # Crop the image to just the playfield.
    playfield = region.crop(image)

    if args.tgm1 or config.getboolean('settings', 'tgm1'):
        playfield_converter = TGM1PlayfieldConverter(region, args.threshold)
    else:
        playfield_converter = PlayfieldConverter(region, args.threshold)
    matrix = playfield_converter.build_matrix(image)
    fumenize(matrix, args.preview or config.getboolean('settings', 'preview'))
