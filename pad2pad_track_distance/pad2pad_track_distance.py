# -*- coding: utf-8 -*-
#  pad2pad_track_distance.py
#
# Copyright (C) 2018 Mitja Nemec
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


import pcbnew
import os
import sys
import logging

SCALE = 1000000.0

logger = logging.getLogger(__name__)

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


class Distance:
    def __init__(self, board, pad1, pad2):

        self.board = board

        self.track_list = []

        # get list of all selected pads
        selected_pads = [pad1, pad2]

        # get the net the pins are on
        net = pad1.GetNetname()

        # find all tracks on the net
        netcode = self.board.GetNetcodeFromNetname(net)
        self.tracks_on_net = self.board.TracksInNet(netcode)

        # starting point and layer
        self.start_point = selected_pads[0].GetPosition()
        # if THT
        if selected_pads[0].GetAttribute() == 0:
            self.start_layer = 'Any'
        else:
            if selected_pads[0].GetParent().IsFlipped():
                self.start_layer = pcbnew.B_Cu
            else:
                self.start_layer = pcbnew.F_Cu

        self.end_point = selected_pads[1].GetPosition()
        # if THT
        if selected_pads[1].GetAttribute() == 0:
            self.end_layer = 'Any'
        else:
            if selected_pads[1].GetParent().IsFlipped():
                self.end_layer = pcbnew.B_Cu
            else:
                self.end_layer = pcbnew.F_Cu

    def get_length(self):
        # current point and layer

        lenght = self.get_new_endpoints(self.start_point, self.start_layer, 0, self.tracks_on_net, 0, ["pad1"])

        length_alt = []
        resistance = []
        # caluclate again
        size = len(self.track_list)
        for i in range(size):
            length_alt.append(0)
            resistance.append(0)
            for track in self.track_list[i][1:-1]:
                length_alt[i] = length_alt[i] + pcbnew.ToMM(track.GetLength())
                track_res = track.GetLength()/SCALE * (0.0000000168*1000) / (0.035 * track.GetWidth()/SCALE)
                resistance[i] = resistance[i] + track_res

        # if connection vas not found, raise an exception
        if not length_alt:
            raise LookupError("Did not find a connection between pads\nThe connection might be partial or through the zone.")

        # find minimum and get only that track list
        min_length = min(length_alt)
        min_res = min(resistance)
        index = length_alt.index(min_length)

        # go through the list and find minimum
        min_length = min(lenght)

        return min_length, min_res

    def get_new_endpoints(self, point, layer, track_length, track_list, level, tl):
        ret_len = []
        index = 0
        tracks_to_do = len(track_list)
        # find track at this endpoint
        for track in track_list:
            tr_list = list(tl)
            new_point = None
            # if via, swap layer
            if track.GetClass() == "VIA":
                tr_list.append(track)
                new_layer = "Any"
                via_point = track.GetPosition()
                if via_point == point:
                    new_point = point
                    # remove current track from list so that we don't iterate over it
                    new_track_list = list(track_list)
                    new_track_list.remove(track)
                    new_track_length = track_length
            else:
                point1 = track.GetStart()
                point2 = track.GetEnd()
                track_layer = track.GetLayer()

                # if on same layer and start at the same point
                # TODO - maybe use track.GetTrack method or track.HitTest(point)
                # TODO - if using hittest, split the tracks if needed
                # todo - add tracks used in calculation to a list
                # todo - select all used tracks and deselect pads (in action plugin only)
                # todo - calculate dc resistance for 35um copper
                # todo - calculate inductance of a trace only
                if (track_layer == layer or layer == "Any") and (point1 == point or point2 == point):
                    if point1 == point:
                        new_point = point2
                    if point2 == point:
                        new_point = point1

                    tr_list.append(track)

                    # remove current track from list so that we don't iterate over it
                    new_track_list = list(track_list)
                    new_track_list.remove(track)
                    new_layer = track.GetLayer()

                    new_track_length = track_length + track.GetLength()/SCALE

                    # check if we arrived to pad2
                    if new_point == self.end_point and (new_layer == self.end_layer or self.end_layer == 'Any'):
                        new_point = None
                        new_layer = None
                        tr_list.append("pad2")
                        self.track_list.append(tr_list)
                        # add to list
                        if len(ret_len) == 0:
                            ret_len = [new_track_length]
                        elif len(ret_len) <= (index + 1):
                            ret_len[index] = new_track_length
                        else:
                            ret_len.append(new_track_length)
                        index = index + 1
                # if there is no track at this point this is a blind end
                else:
                    new_point = None
                    new_layer = None
            # ce se nismo na koncu, potem grem naprej
            if new_point is not None:
                delta_len = self.get_new_endpoints(new_point, new_layer, new_track_length, new_track_list, level + 1, tr_list)
                if any(delta_len):
                    ret_len[index:index] = delta_len
                    pass
        return ret_len


def test(board, pad1, pad2):
    measure_distance = Distance(board, pad1, pad2)
    distance, resistance = measure_distance.get_length()

    return distance, resistance


def main():

    # test_board = "trivial"
    board = pcbnew.LoadBoard('En_mostic_test.kicad_pcb')
    module_1 = board.FindModuleByReference("R2")
    pad1 = module_1.FindPadByName("2")
    module_2 = board.FindModuleByReference("R3")
    pad2 = module_2.FindPadByName("1")
    dist, res = test(board, pad1, pad2)
    assert(-0.1 < (dist-4.767) < +0.1)

    # test_board == "easy1"
    module_1 = board.FindModuleByReference("U3")
    pad1 = module_1.FindPadByName("8")
    module_2 = board.FindModuleByReference("U1")
    pad2 = module_2.FindPadByName("15")
    dist, res = test(board, pad1, pad2)
    assert(-0.1 < (dist-19.833) < +0.1)

    # test_board == "easy2"
    module_1 = board.FindModuleByReference("U6")
    pad1 = module_1.FindPadByName("8")
    module_2 = board.FindModuleByReference("U1")
    pad2 = module_2.FindPadByName("7")
    dist, res = test(board, pad1, pad2)
    assert(-0.1 < (dist-16.124) < +0.1)


    # test_board == "medium1":
    module_1 = board.FindModuleByReference("U1")
    pad1 = module_1.FindPadByName("48")
    module_2 = board.FindModuleByReference("J2")
    pad2 = module_2.FindPadByName("2")
    dist, res = test(board, pad1, pad2)
    assert(-0.1 < (dist-18.58) < +0.1)

    # test_board == "medium2":
    module_1 = board.FindModuleByReference("U4")
    pad1 = module_1.FindPadByName("7")
    module_2 = board.FindModuleByReference("U4")
    pad2 = module_2.FindPadByName("9")
    dist, res = test(board, pad1, pad2)
    # assert(-0.1 < (dist-5.074) < +0.1) # 14.21

    # test_board == 'hard':
    module_1 = board.FindModuleByReference("U2")
    pad1 = module_1.FindPadByName("2")
    module_2 = board.FindModuleByReference("U3")
    pad2 = module_2.FindPadByName("7")
    dist, res = test(board, pad1, pad2)
    # assert(-0.1 < (dist-29.341) < +0.1) # 37.65
    """
    # THT
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_files"))
    board = pcbnew.LoadBoard('g3ruh-modem.kicad_pcb')
    module_1 = board.FindModuleByReference("U1")
    pad1 = module_1.FindPadByName("1")
    module_2 = board.FindModuleByReference("U2")
    pad2 = module_2.FindPadByName("2")
    dist, res = test(board, pad1, pad2)
    assert(-0.1 < (dist-12.264) < +0.1)
    """


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='pad2pad_distance.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("pad2pad distance plugin version: " + VERSION + " started in standalone mode")

    main()
