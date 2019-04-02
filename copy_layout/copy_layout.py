# -*- coding: utf-8 -*-
#  replicate_layout_V2.py
#
# Copyright (C) 2019 Mitja Nemec, Stephen Walker-Weinshenker
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
from __future__ import absolute_import, division, print_function
import pcbnew
from collections import namedtuple
import os
import sys
import logging
import itertools
import re
import math

Module = namedtuple('Module', ['ref', 'mod', 'mod_id', 'sheet_id', 'filename'])
logger = logging.getLogger(__name__)


def export_layout(old_file, new_file):
    # load the old board
    old_board = pcbnew.LoadBoard(old_file)
    # save as new board
    saved = pcbnew.SaveBoard(new_file, old_board)
    new_board = pcbnew.LoadBoard(new_file)
    # remove everything from new board
    new_modules = new_board.GetModules()
    for mod in new_modules:
        new_board.DeleteNative(mod)

    new_tracks = new_board.GetTracks()
    for track in new_tracks:
        new_board.DeleteNative(track)

    zones = new_board.Zones()
    for zone in zones:
        new_board.DeleteNative(zone)

    dwgs = new_board.GetDrawings()
    for dwg in dwgs:
        new_board.DeleteNative(dwg)
    pass

    nets = new_board.GetNetInfo()
    nets_by_name = nets.NetsByName()
    nets_by_name.clear()

    # erase all netclasses, leave the deafult but leave it empty
    # TODO
    saved = pcbnew.SaveBoard(new_file, new_board)
    new_board = pcbnew.LoadBoard(new_file)

    # I have a clear board available

    # load schematics and calculate hash of schematics (you have to support nested hierarchy)
    # append hash to new_board filename, so that can be checked on import

    # place all the footprinst from old_board to new_board
    # place all tracks from old_board to new_board
    # place all zones from old_board to new_board
    # place all drawings from old_board to new_board


def import_layout():
    pass


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Source_project"))
    input_file = 'Source_project.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp"+".kicad_pcb"
    export_layout(input_file, output_file)
    pass


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='copy_layout.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Copy layout plugin started in standalone mode")

    main()