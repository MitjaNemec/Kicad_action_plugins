#  replicatelayout.py
#
# Copyright (C) 2017 Mitja Nemec
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
from sets import Set

SCALE = 1000000

# helper functions

def get_module_id(module):
    """ get module id"""
    module_path = module.GetPath().split('/')
    module_id = "/".join(module_path[-1:])
    return module_id

    
def get_sheet_id(module):
    """ get sheet id"""
    module_path = module.GetPath().split('/')
    sheet_id = "/".join(module_path[0:-1])
    return sheet_id


# this function was made by Miles Mccoo
# https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
def coordsFromPolySet(ps):
    str = ps.Format()
    lines = str.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]]  # -1 because of the extra two \n
    return pts

    
class Replicator:
    def __init__(self, board, pivot_module_reference, only_within_boundingbox):
        """ initialize base object needed to replicate module layout, track layout and zone layout"""
        # take care of different APIs
        if hasattr(pcbnew, "LAYER_ID_COUNT"):
            pcbnew.PCB_LAYER_ID_COUNT = pcbnew.LAYER_ID_COUNT

        self.board = board

        # load all modules
        self.modules = board.GetModules()

        # find pivodmodule
        self.pivot_mod = board.FindModuleByReference(pivot_module_reference)

        # find sheet ID on which the module is on
        self.pivot_sheet_id = get_sheet_id(self.pivot_mod)

        # while at it, get the pivot module ID
        self.pivot_mod_id = get_module_id(self.pivot_mod)

        # find all modules on the same sheet
        self.pivot_modules = []
        self.pivot_modules_id = []
        for mod in self.modules:
            module_id = get_module_id(mod)
            sheet_id = get_sheet_id(mod)
            if sheet_id == self.pivot_sheet_id:
                self.pivot_modules.append(mod)
                self.pivot_modules_id.append(module_id)

        # find all sheets to replicate
        self.sheets_to_clone = []
        for mod in self.modules:
            module_id = get_module_id(mod)
            sheet_id = get_sheet_id(mod)
            if (module_id == self.pivot_mod_id) and (sheet_id != self.pivot_sheet_id) \
                    and (sheet_id not in self.sheets_to_clone):
                self.sheets_to_clone.append(sheet_id)
        pass

        # get bounding bounding box of all modules
        bounding_box = self.pivot_mod.GetBoundingBox()
        top = bounding_box.GetTop()
        bottom = bounding_box.GetBottom()
        left = bounding_box.GetLeft()
        right = bounding_box.GetRight()
        for mod in self.pivot_modules:
            mod_box = mod.GetBoundingBox()
            top = min(top, mod_box.GetTop())
            bottom = max(bottom, mod_box.GetBottom())
            left = min(left, mod_box.GetLeft())
            right = max(right, mod_box.GetRight())

        position = pcbnew.wxPoint(left, top)
        size = pcbnew.wxSize(right - left, bottom - top)
        self.pivot_bounding_box = pcbnew.EDA_RECT(position, size)

        # find all tracks within the pivot bounding box
        all_tracks = board.GetTracks()
        # keep only tracks that are within our bounding box
        self.pivot_tracks = []
        for track in all_tracks:
            track_bb = track.GetBoundingBox()
            if only_within_boundingbox:
                if self.pivot_bounding_box.Contains(track_bb):
                    self.pivot_tracks.append(track)
            else:
                if self.pivot_bounding_box.Intersects(track_bb):
                    self.pivot_tracks.append(track)
        # get all zones
        all_zones = []
        for zoneid in range(board.GetAreaCount()):
            all_zones.append(board.GetArea(zoneid))
        # find all zones which are completely within the pivot bounding box
        self.pivot_zones = []
        for zone in all_zones:
            zone_bb = zone.GetBoundingBox()
            if only_within_boundingbox:
                if self.pivot_bounding_box.Contains(zone_bb):
                    self.pivot_zones.append(zone)
            else:
                if self.pivot_bounding_box.Intersects(zone_bb):
                    self.pivot_zones.append(zone)

    def get_net_pairs(self, sheet_id):
        """ find all net pairs between pivot sheet and current sheet"""
        # find all modules, pads and nets on this sheet
        sheet_pads = []
        sheet_modules = []
        sheet_nets = Set([])
        for mod in self.modules:
            mod_sheet_id = get_sheet_id(mod)
            if mod_sheet_id == sheet_id:
                sheet_modules.append(mod)
                for pad in mod.PadsList():
                    sheet_pads.append(pad)
                    net = pad.GetNetname()
                    sheet_nets.add(net)
        sheet_nets_list = []
        for net in sheet_nets:
            sheet_nets_list.append((net, net.split('/')))
        # find all net pairs via same modules pads,
        net_pairs = []
        net_dict = {}
        # go through pivot modules
        for p_mod in self.pivot_modules:
            # and thorught sheet modules
            for s_mod in sheet_modules:
                # find a pair of modules
                if get_module_id(p_mod) == get_module_id(s_mod):
                    # get their pads
                    p_mod_pads = p_mod.PadsList()
                    s_mod_pads = s_mod.PadsList()
                    # I am going to assume pads are in the same order
                    p_nets = []
                    s_nets = []
                    # get nelists for each pad
                    for p_pad in p_mod_pads:
                        p_nets.append(p_pad.GetNetname())
                    for s_pad in s_mod_pads:
                        s_nets.append(s_pad.GetNetname())
                        net_dict[s_pad.GetNetname()] = s_pad.GetNet()
                    # build list of net tupules
                    for net in p_nets:
                        index = p_nets.index(net)
                        net_pairs.append((p_nets[index], s_nets[index]))

        # remove duplicates
        net_pairs_clean = []
        for i in net_pairs:
            if i not in net_pairs_clean:
                net_pairs_clean.append(i)

        return net_pairs_clean, net_dict

    def replicate_modules(self, x_offset, y_offset):
        global SCALE
        """ method which replicates modules"""
        for sheet in self.sheets_to_clone:
            sheet_index = self.sheets_to_clone.index(sheet) + 1
            # begin with modules
            for mod in self.modules:
                module_path = mod.GetPath().split('/')
                module_id = "/".join(module_path[-1:])
                sheet_id = "/".join(module_path[0:-1])
                # if module is on selected sheet
                if sheet_id == sheet:
                    # find which is the corresponding pivot module
                    if module_id in self.pivot_modules_id:
                        # get coresponding pivot module and its position
                        index = self.pivot_modules_id.index(module_id)
                        mod_to_clone = self.pivot_modules[index]
                        pivod_mod_position = mod_to_clone.GetPosition()
                        pivod_mod_orientation = mod_to_clone.GetOrientation()
                        pivot_mod_flipped = mod_to_clone.IsFlipped()

                        # get new position
                        newposition = (int(pivod_mod_position[0] + sheet_index * x_offset * SCALE),
                                       int(pivod_mod_position[1] + sheet_index * y_offset * SCALE))

                        # place current module
                        mod.SetPosition(pcbnew.wxPoint(*newposition))
                        mod.SetOrientation(pivod_mod_orientation)
                        if (mod.IsFlipped() and not pivot_mod_flipped) or (pivot_mod_flipped and not mod.IsFlipped()):
                            mod.Flip(mod.GetPosition())

    def replicate_tracks(self, x_offset, y_offset):
        """ method which replicates tracks"""
        global SCALE
        # start cloning
        for sheet in self.sheets_to_clone:
            sheet_index = self.sheets_to_clone.index(sheet) + 1
            net_pairs, net_dict = self.get_net_pairs(sheet)

            # go through all the tracks
            for track in self.pivot_tracks:
                # get from which net we are clonning
                from_net_name = track.GetNetname()
                # find to net
                to_net_name = [item for item in net_pairs if item[0] == from_net_name][0][1]
                to_net = net_dict[to_net_name]

                # finally make a copy
                # this came from Miles Mccoo
                # https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
                if track.GetClass() == "VIA":
                    oldvia = self.board.GetViaByPosition(track.GetPosition())
                    newvia = pcbnew.VIA(self.board)
                    # need to add before SetNet will work, so just doing it first
                    self.board.Add(newvia)
                    toplayer = -1
                    bottomlayer = pcbnew.PCB_LAYER_ID_COUNT
                    for l in range(pcbnew.PCB_LAYER_ID_COUNT):
                        if not track.IsOnLayer(l):
                            continue
                        toplayer = max(toplayer, l)
                        bottomlayer = min(bottomlayer, l)
                    newvia.SetLayerPair(toplayer, bottomlayer)
                    newvia.SetPosition(pcbnew.wxPoint(track.GetPosition().x + sheet_index*x_offset*SCALE,
                                                      track.GetPosition().y + sheet_index*y_offset*SCALE))
                    newvia.SetViaType(oldvia.GetViaType())
                    newvia.SetWidth(oldvia.GetWidth())
                    newvia.SetNet(to_net)
                else:
                    newtrack = pcbnew.TRACK(self.board)
                    # need to add before SetNet will work, so just doing it first
                    self.board.Add(newtrack)
                    newtrack.SetStart(pcbnew.wxPoint(track.GetStart().x + sheet_index*x_offset*SCALE,
                                                     track.GetStart().y + sheet_index*y_offset*SCALE))
                    newtrack.SetEnd(pcbnew.wxPoint(track.GetEnd().x + sheet_index*x_offset*SCALE,
                                                   track.GetEnd().y + sheet_index*y_offset*SCALE))
                    newtrack.SetWidth(track.GetWidth())
                    newtrack.SetLayer(track.GetLayer())

                    newtrack.SetNet(to_net)
                pass

    def replicate_zones(self, x_offset, y_offset):
        """ method which replicates zones"""
        global SCALE
        # start cloning
        for sheet in self.sheets_to_clone:
            sheet_index = self.sheets_to_clone.index(sheet) + 1
            net_pairs, net_dict = self.get_net_pairs(sheet)
            # go through all the zones
            for zone in self.pivot_zones:
                # get from which net we are clonning
                from_net_name = zone.GetNetname()
                # find to net
                to_net_name = [item for item in net_pairs if item[0] == from_net_name][0][1]
                to_net = net_dict[to_net_name]

                # now I can finally make a copy of a zone
                # this came from Miles Mccoo
                # https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
                coords = coordsFromPolySet(zone.Outline())
                newzone = self.board.InsertArea(to_net.GetNet(),
                                                0,
                                                zone.GetLayer(),
                                                coords[0][0] + int(sheet_index*x_offset*SCALE),
                                                coords[0][1] + int(sheet_index*y_offset*SCALE),
                                                pcbnew.CPolyLine.DIAGONAL_EDGE)
                newoutline = newzone.Outline()
                for pt in coords[1:]:
                    newoutline.Append(pt[0] + int(sheet_index*x_offset*SCALE), pt[1] + int(sheet_index*y_offset*SCALE))
                newzone.Hatch()

    def replicate_layout(self, x_offset, y_offset):
        self.replicate_modules(x_offset, y_offset)
        self.replicate_tracks(x_offset, y_offset)
        self.replicate_zones(x_offset, y_offset)


def main():
    # required for file comparison
    import difflib

    # load test board
    board = pcbnew.LoadBoard('test_board.kicad_pcb')
    # run the replicator
    replicator = Replicator(board=board, pivot_module_reference='Q2002', only_within_boundingbox=True)
    replicator.replicate_layout(22.860, 0.0)
    # save the board
    saved = pcbnew.SaveBoard('unit_test_only_within.kicad_pcb', board)

    # compare files
    errnum_within = 0
    with open('test_board_only_within.kicad_pcb', 'r') as correct_board:
        with open('unit_test_only_within.kicad_pcb', 'r') as tested_board:
            diff = difflib.unified_diff(
                correct_board.readlines(),
                tested_board.readlines(),
                fromfile='correct_board',
                tofile='tested_board',
                n=0)
    # only timestamps on zones and file version information should differ
    diffstring = []
    for line in diff:
        diffstring.append(line)
    # get rid of diff information
    del diffstring[0]
    del diffstring[0]
    # walktrough diff list and check for any significant differences
    for line in diffstring:
        index = diffstring.index(line)
        if '@@' in line:
            if  ((('version' in diffstring[index + 1]) and
                 ('version' in diffstring[index + 2])) or
                (('tstamp' in diffstring[index + 1]) and
                 ('tstamp' in diffstring[index + 2]))):
                # this is not a problem
                pass
            else:
                # this is a problem
                errnum_within = errnum_within + 1

    # load test board
    board = pcbnew.LoadBoard('test_board.kicad_pcb')
    # run the replicator
    replicator = Replicator(board=board, pivot_module_reference='Q2002', only_within_boundingbox=False)
    replicator.replicate_layout(22.860, 0.0)
    # save the board
    saved = pcbnew.SaveBoard('unit_test_all.kicad_pcb', board)
    # compare files
    errnum_all = 0
    with open('test_board_all.kicad_pcb', 'r') as correct_board:
        with open('unit_test_all.kicad_pcb', 'r') as tested_board:
            diff = difflib.unified_diff(
                correct_board.readlines(),
                tested_board.readlines(),
                fromfile='correct_board',
                tofile='tested_board',
                n=0)
    # only timestamps on zones and file version information should differ
    diffstring = []
    for line in diff:
        diffstring.append(line)
    # get rid of diff information
    del diffstring[0]
    del diffstring[0]
    # walktrough diff list and check for any significant differences
    for line in diffstring:
        index = diffstring.index(line)
        if '@@' in line:
            if  ((('version' in diffstring[index + 1]) and
                 ('version' in diffstring[index + 2])) or
                (('tstamp' in diffstring[index + 1]) and
                 ('tstamp' in diffstring[index + 2]))):
                # this is not a problem
                pass
            else:
                # this is a problem
                errnum_all = errnum_all + 1
    if errnum_all == 0 and errnum_within == 0:
        print "passed all tests"
    if errnum_all == 0 and errnum_within != 0:
        print "failed replicating only containing sheet"
    if errnum_all != 0 and errnum_within == 0:
        print "failed replicating complete (with intersections) sheet"
    if errnum_all != 0 and errnum_within != 0:
        print "failed all tests"

# for testing purposes only
if __name__ == "__main__":
    main()
