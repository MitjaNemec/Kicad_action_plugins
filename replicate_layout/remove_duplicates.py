# -*- coding: utf-8 -*-
#  remove_duplicates.py
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
import os
import sys
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


def zones_equal(zone1, zone2):
    z1_layer = zone1.GetLayer()
    z1_corners = zone1.GetNumCorners()

    z2_layer = zone2.GetLayer()
    z2_corners = zone2.GetNumCorners()

    if z1_layer == z2_layer:
        if z1_corners == z2_corners:
            z1_corners = [zone1.GetCornerPosition(index) for index in range(z1_corners)]
            z2_corners = [zone2.GetCornerPosition(index) for index in range(z2_corners)]
            z1z2_corners = zip(z1_corners, z2_corners)
            if all(x[0] == x[1] for x in z1z2_corners):
                return 1
    return 0


def remove_duplicate_zones(board):
    # load all zones
    zones = board.Zones()

    # build a dictionary wih a list of tracks for each net
    zone_dict = defaultdict(list)
    for zone in zones:
        zone_dict[zone.GetNetCode()].append(zone)

    # go through all the keys
    for key in zone_dict:
        zones = zone_dict[key]

        # for each key compare each track agianst each other and if there is no equal
        # remove it from the list and add to the new list

        for index in range(len(zones)):
            z1 = zones[index]
            bools = map(lambda x: zones_equal(x, z1), zones[index+1:])
            if sum(bools) != 0:
                board.RemoveNative(z1)


def tracks_equal(track1, track2):
    t1_layer = track1.GetLayer()
    t1_pos = track1.GetPosition()
    t1_start = track1.GetStart()
    t1_end = track1.GetEnd()

    t2_layer = track2.GetLayer()
    t2_pos = track2.GetPosition()
    t2_start = track2.GetStart()
    t2_end = track2.GetEnd()

    if t1_layer == t2_layer:
        if t1_pos == t2_pos:
            if t1_start == t2_start:
                if t1_end == t2_end:
                    return 1
    return 0


def remove_duplicate_tracks(board):
    # load all tracks
    tracks = board.GetTracks()

    # build a dictionary wih a list of tracks for each net
    track_dict = defaultdict(list)
    for track in tracks:
        track_dict[track.GetNetCode()].append(track)

    # go through all the keys
    for key in track_dict:
        tracks = track_dict[key]

        # for each key compare each track agianst each other and if there is no equal
        # remove it from the list and add to the new list

        for index in range(len(tracks)):
            t1 = tracks[index] 
            bools = map(lambda x: tracks_equal(x, t1), tracks[index+1:])
            if sum(bools) != 0:
                board.RemoveNative(t1)


def text_equal(text1, text2):
    t1_properties = []
    t1_properties.append(text1.GetLayer())
    t1_properties.append(text1.GetPosition())
    t1_properties.append(text1.GetTextPos())
    t1_properties.append(text1.GetText())
    t1_properties.append(text1.GetThickness())
    t1_properties.append(text1.GetTextAngle())
    t1_properties.append(text1.IsItalic())
    t1_properties.append(text1.IsBold())
    t1_properties.append(text1.IsVisible())
    t1_properties.append(text1.IsMirrored())
    t1_properties.append(text1.GetVertJustify())
    t1_properties.append(text1.GetHorizJustify())
    t1_properties.append(text1.GetTextSize())
    t1_properties.append(text1.GetTextWidth())
    t1_properties.append(text1.GetTextHeight())

    t2_properties = []
    t2_properties.append(text2.GetLayer())
    t2_properties.append(text2.GetPosition())
    t2_properties.append(text2.GetTextPos())
    t2_properties.append(text2.GetText())
    t2_properties.append(text2.GetThickness())
    t2_properties.append(text2.GetTextAngle())
    t2_properties.append(text2.IsItalic())
    t2_properties.append(text2.IsBold())
    t2_properties.append(text2.IsVisible())
    t2_properties.append(text2.IsMirrored())
    t2_properties.append(text2.GetVertJustify())
    t2_properties.append(text2.GetHorizJustify())
    t2_properties.append(text2.GetTextSize())
    t2_properties.append(text2.GetTextWidth())
    t2_properties.append(text2.GetTextHeight())

    t1t2_properties = zip(t1_properties, t2_properties)
    if all(x[0] == x[1] for x in t1t2_properties):
        return 1
    return 0


def remove_duplicate_text(board):
    # load text items
    drawings = board.GetDrawings()

    text_items = []
    for drawing in drawings:
        if isinstance(drawing, pcbnew.TEXTE_PCB):
            text_items.append(drawing)

    for index in range(len(text_items)):
        t1 = text_items[index]
        bools = map(lambda x: text_equal(x, t1), text_items[index+1:])
        if sum(bools) != 0:
            board.RemoveNative(t1)


def drawings_equal(drawing1, drawing2):
    d1_properties = []
    d1_properties.append(drawing1.GetLayer())
    d1_properties.append(drawing1.GetPosition())
    d1_properties.append(drawing1.GetStart())
    d1_properties.append(drawing1.GetEnd())
    d1_properties.append(drawing1.GetClass())
    d1_properties.append(drawing1.GetLength())
    d1_properties.append(drawing1.GetWidth())
    d1_properties.append(drawing1.GetAngle())
    d1_properties.append(drawing1.GetType())
    d1_properties.append(drawing1.GetShape())

    d2_properties = []
    d2_properties.append(drawing2.GetLayer())
    d2_properties.append(drawing2.GetPosition())
    d2_properties.append(drawing2.GetStart())
    d2_properties.append(drawing2.GetEnd())
    d2_properties.append(drawing2.GetClass())
    d2_properties.append(drawing2.GetLength())
    d2_properties.append(drawing2.GetWidth())
    d2_properties.append(drawing2.GetAngle())
    d2_properties.append(drawing2.GetType())
    d2_properties.append(drawing2.GetShape())

    d1d2_properties = zip(d1_properties, d2_properties)
    if all(x[0] == x[1] for x in d1d2_properties):
        return 1
    return 0


def remove_duplicate_drawings(board):
    # load text items
    drawings = board.GetDrawings()

    drawing_items = []
    for drawing in drawings:
        if isinstance(drawing, pcbnew.DRAWSEGMENT):
            drawing_items.append(drawing)

    for index in range(len(drawing_items)):
        d1 = drawing_items[index]
        bools = map(lambda x: drawings_equal(x, d1), drawing_items[index+1:])
        if sum(bools) != 0:
            board.RemoveNative(d1)


def remove_duplicates(board):
    # remove duplicate tracks
    remove_duplicate_tracks(board)
    # remove duplicate zones
    remove_duplicate_zones(board)
    # remove duplicate text
    remove_duplicate_text(board)
    # remove duplicate drawings
    remove_duplicate_drawings(board)


def main():
    board = pcbnew.LoadBoard("multiple_hierarchy_duplicated.kicad_pcb")
    remove_duplicates(board)
    pcbnew.SaveBoard("multiple_hierarchy_duplicated_test.kicad_pcb", board)


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='delete_duplicates.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("Delete duplicates plugin started in standalone mode")

    main()



