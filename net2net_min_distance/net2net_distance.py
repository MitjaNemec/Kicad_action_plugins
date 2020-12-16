# -*- coding: utf-8 -*-
#  net2net_distance.py
#
# Copyright (C) 2019 Mitja Nemec
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
import os
import logging
import pcbnew
import sys
import math

logger = logging.getLogger(__name__)
SCALE = 1000000.0

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


def segments_distance(x11, y11, x12, y12, x21, y21, x22, y22):
    """ distance between two segments in the plane:
        one segment is (x11, y11) to (x12, y12)
        the other is   (x21, y21) to (x22, y22)
    """
    if segments_intersect(x11, y11, x12, y12, x21, y21, x22, y22):
        return 0
    # try each of the 4 vertices w/the other segment
    distances = []
    distances.append(point_segment_distance(x11, y11, x21, y21, x22, y22))
    distances.append(point_segment_distance(x12, y12, x21, y21, x22, y22))
    distances.append(point_segment_distance(x21, y21, x11, y11, x12, y12))
    distances.append(point_segment_distance(x22, y22, x11, y11, x12, y12))
    logger.info("All distances:\n" + repr(distances))
    return min(distances, key=lambda t: t[0])


def segments_intersect(x11, y11, x12, y12, x21, y21, x22, y22):
    """ whether two segments in the plane intersect:
        one segment is (x11, y11) to (x12, y12)
        the other is   (x21, y21) to (x22, y22)
    """
    dx1 = x12 - x11
    dy1 = y12 - y11
    dx2 = x22 - x21
    dy2 = y22 - y21
    delta = dx2 * dy1 - dy2 * dx1
    if delta == 0:
        return False  # parallel segments
    s = (dx1 * (y21 - y11) + dy1 * (x11 - x21)) / delta
    t = (dx2 * (y11 - y21) + dy2 * (x21 - x11)) / (-delta)

    return (0 <= s <= 1) and (0 <= t <= 1)


def point_segment_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == dy == 0:  # the segment's just a point
        return math.hypot(px - x1, py - y1)

    # Calculate the t that minimizes the distance.
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)

    # See if this represents one of the segment's
    # end points or a point in the middle.
    if t < 0:
        dx = px - x1
        dy = py - y1
    elif t > 1:
        dx = px - x2
        dy = py - y2
    else:
        near_x = x1 + t * dx
        near_y = y1 + t * dy
        dx = px - near_x
        dy = py - near_y
    location = (px, py, int(px+dx), int(py+dy))

    return math.hypot(dx, dy), location


def get_min_distance(board, nets):
    # get nets
    net1 = nets[0]
    net2 = nets[1]
    logger.info("Net2net getting min distance between " + str(net1) + " and " + str(net2))

    # get tracks on net
    tracks_1 = []
    tracks_2 = []
    all_tracks = board.GetTracks()
    for track in all_tracks:
        if track.GetNetname() == net1:
            tracks_1.append(track)
        if track.GetNetname() == net2:
            tracks_2.append(track)

    logger.info("Found " + str(len(tracks_1)+1) + " tracks on " + str(net1) + " and " + str(len(tracks_2)+1) + "tracks on " + str(net2))
    # TODO maybe I have to raise an exception if there ar no tracks on either net

    min_distance = None
    location = None
    for track1 in tracks_1:
        w1 = track1.GetWidth()
        x11 = track1.GetStart().x
        y11 = track1.GetStart().y
        x12 = track1.GetEnd().x
        y12 = track1.GetEnd().y
        for track2 in tracks_2:
            w2 = track2.GetWidth()
            x21 = track2.GetStart().x
            y21 = track2.GetStart().y
            x22 = track2.GetEnd().x
            y22 = track2.GetEnd().y
            dis, loc = segments_distance(x11, y11, x12, y12, x21, y21, x22, y22)
            dis = dis - w1/2 - w2/2
            if min_distance is None:
                min_distance = dis
                location = tuple(loc)
            if min_distance > dis:
                min_distance = dis
                location = tuple(loc)

    # if location was not set we assume there are zero tracks on either net
    if location is None:
        min_distance = float('Nan')
        location = (float('Nan'), float('Nan'), float('Nan'), float('Nan'))

    return min_distance, location


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "net2net_test"))
    logger.info("Testing net2net")
    input_file = 'net2net_test.kicad_pcb'

    board = pcbnew.LoadBoard(input_file)
    mod = board.FindModuleByReference('R101')
    pads = mod.Pads()
    for pad in pads:
        if pad.GetPadName() == u'2':
            pad1_net = pad.GetNetname()
    mod = board.FindModuleByReference('R102')
    pads = mod.Pads()
    for pad in pads:
        if pad.GetPadName() == u'2':
            pad2_net = pad.GetNetname()

    dis, loc = get_min_distance(board, [pad1_net, pad2_net])


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='net2net_min_distance.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    # handlers = [file_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("Net2net plugin version: " + VERSION + " started in standalone mode")

    main()