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

import wx
import pcbnew

SCALE = 1000000.0


class Distance:
    def __init__(self, board, pad1, pad2):

        self.board = board

        self.track_list = []

        # get list of all selected pads
        selected_pads = [pad1, pad2]

        # get the net the pins are on
        net = pad1.GetNetname()

        # poisci vse track-e
        tracks = board.GetTracks()
                
        # poisci samo track-e ki so na pravem net-u
        self.tracks_on_net = []
        for track in tracks:
            track_net_name = track.GetNetname()
            if track_net_name == net:
                self.tracks_on_net.append(track)

        # starting point and layer
        self.start_point = selected_pads[0].GetPosition()
        if selected_pads[0].GetParent().IsFlipped():
            self.start_layer = pcbnew.B_Cu
        else:
            self.start_layer = pcbnew.F_Cu

        self.end_point = selected_pads[1].GetPosition()
        if selected_pads[1].GetParent().IsFlipped():
            self.end_layer = pcbnew.B_Cu
        else:
            self.end_layer = pcbnew.F_Cu

    def get_length(self):
        # current point and layer

        lenght = self.get_new_endpoints(self.start_point, self.start_layer, 0, self.tracks_on_net, 0, ["pad1"])

        length_alt = []
        # caluclate again
        size = len(self.track_list)
        for i in range(size):
            length_alt.append(0)
            for track in self.track_list[i][1:-1]:
                length_alt[i] = length_alt[i] + pcbnew.ToMM(track.GetLength())

        # find minimum and get only that track list
        min_length = min(length_alt)
        index = length_alt.index(min_length)
        tracks = self.track_list[index][1:-1]

        # go through the list and find minimum
        min_length = min(lenght)

        return min_length

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
                    if new_point == self.end_point and new_layer == self.end_layer:
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


def main():
    board = pcbnew.LoadBoard('En_mostic_test.kicad_pcb')

    # get all pads
    modules = board.GetModules()
    test_board = "trivial"
    if test_board == 'trivial':
        module_1 = board.FindModuleByReference("R2")
        pad1 = module_1.FindPadByName("2")
        module_2 = board.FindModuleByReference("R3")
        pad2 = module_2.FindPadByName("1")
    elif test_board == "easy1":
        module_1 = board.FindModuleByReference("U3")
        pad1 = module_1.FindPadByName("8")
        module_2 = board.FindModuleByReference("U1")
        pad2 = module_2.FindPadByName("15")
    elif test_board == "easy2":
        module_1 = board.FindModuleByReference("U6")
        pad1 = module_1.FindPadByName("8")
        module_2 = board.FindModuleByReference("U1")
        pad2 = module_2.FindPadByName("7")
    elif test_board == "medium1":
        module_1 = board.FindModuleByReference("U1")
        pad1 = module_1.FindPadByName("48")
        module_2 = board.FindModuleByReference("J2")
        pad2 = module_2.FindPadByName("2")
    elif test_board == "medium2":
        module_1 = board.FindModuleByReference("U4")
        pad1 = module_1.FindPadByName("7")
        module_2 = board.FindModuleByReference("U4")
        pad2 = module_2.FindPadByName("9")
    elif test_board == 'hard':
        module_1 = board.FindModuleByReference("U2")
        pad1 = module_1.FindPadByName("2")
        module_2 = board.FindModuleByReference("U3")
        pad2 = module_2.FindPadByName("7")

    measure_distance = Distance(board, pad1, pad2)
    distance = measure_distance.get_length()
    print str(distance)
    # trivial = 4.767; easy = 19.833;  easy2 = 16.124;
    # medium1 = 18.58; medium2 = 5.074 ;hard = 29.341


# for testing purposes only
if __name__ == "__main__":
    main()