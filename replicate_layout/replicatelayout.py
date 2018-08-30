#  replicatelayout.py
#
# Copyright (C) 2018 Mitja Nemec, Stephen Walker-Weinshenker
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
import math
import os
import re

SCALE = 1000000.0


def get_module_id(module):
    """ get module id """
    module_path = module.GetPath().split('/')
    module_id = "/".join(module_path[-1:])
    return module_id


def get_sheet_id(module):
    """ get sheet id """
    module_path = module.GetPath().split('/')
    sheet_id = module_path[0:-1]
    sheet_id = [x for x in sheet_id if x]
    return sheet_id


def rotate_around_center(coordinates, angle):
    """ rotate coordinates for a defined angle in degrees around coordinate center"""
    new_x = coordinates[0] * math.cos(2 * math.pi * angle/360)\
          - coordinates[1] * math.sin(2 * math.pi * angle/360)
    new_y = coordinates[0] * math.sin(2 * math.pi * angle/360)\
          + coordinates[1] * math.cos(2 * math.pi * angle/360)
    return new_x, new_y


def rotate_around_pivot_point(old_position, pivot_point, angle):
    """ rotate coordinates for a defined angle in degrees around a pivot point """
    # get relative position to pivot point
    rel_x = old_position[0] - pivot_point[0]
    rel_y = old_position[1] - pivot_point[1]
    # rotate around
    new_rel_x, new_rel_y = rotate_around_center((rel_x, rel_y), angle)
    # get absolute position
    new_position = (new_rel_x + pivot_point[0], new_rel_y + pivot_point[1])
    return new_position


def get_module_text_items(module):
    """ get all text item belonging to a modules """
    list_of_items = [module.Reference(), module.Value()]

    module_items = module.GraphicalItemsList()
    for item in module_items:
        if type(item) is pcbnew.TEXTE_MODULE:
            list_of_items.append(item)
    return list_of_items


def get_bounding_box_of_modules(module_list):
    """ get bounding box encompasing all modules """
    top = None
    bottom = None
    left = None
    right = None
    for mod in module_list:
        if top is None:
            bounding_box = mod.GetFootprintRect()
            top = bounding_box.GetTop()
            bottom = bounding_box.GetBottom()
            left = bounding_box.GetLeft()
            right = bounding_box.GetRight()
        else:
            mod_box = mod.GetFootprintRect()
            top = min(top, mod_box.GetTop())
            bottom = max(bottom, mod_box.GetBottom())
            left = min(left, mod_box.GetLeft())
            right = max(right, mod_box.GetRight())

    position = pcbnew.wxPoint(left, top)
    size = pcbnew.wxSize(right - left, bottom - top)
    bounding_box = pcbnew.EDA_RECT(position, size)
    return bounding_box


def get_index_of_tuple(list_of_tuples, index, value):
    for pos, t in enumerate(list_of_tuples):
        if t[index] == value:
            return pos

    # Matches behavior of list.index
    raise ValueError("list.index(x): x not in list")


# this function was made by Miles Mccoo
# https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
def get_coordinate_points_of_shape_poly_set(ps):
    string = ps.Format()
    lines = string.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]]  # -1 because of the extra two \n
    return pts


class Replicator:
    def __init__(self, board, pivot_module_reference):
        """ initialize base object needed to replicate module layout, track layout and zone layout"""
        # take care of different APIs
        if hasattr(pcbnew, "LAYER_ID_COUNT"):
            pcbnew.PCB_LAYER_ID_COUNT = pcbnew.LAYER_ID_COUNT

        self.board = board

        # load all modules
        self.modules = board.GetModules()

        # find pivodmodule
        self.pivot_mod = board.FindModuleByReference(pivot_module_reference)

        # while at it, get the pivot module ID
        self.pivot_mod_id = get_module_id(self.pivot_mod)

        # find sheet ID on which the module is on
        self.pivot_sheet_sel_id = get_sheet_id(self.pivot_mod)

        self.project_path = os.path.dirname(os.path.abspath(self.board.GetFileName()))
        layout_filename = os.path.abspath(board.GetFileName())
        filename = layout_filename.replace("kicad_pcb", "sch")
        list_of_sheets = []
        sheet_names = list(set(self.find_all_sch_files(filename, list_of_sheets)))

        self.sheet_levels = []
        for level in self.pivot_sheet_sel_id:
            for sheet in sheet_names:
                if level in sheet[1]:
                    self.sheet_levels.append((sheet[0], level))

        self.pivot_modules = []
        self.pivot_modules_id = []
        self.pivot_modules_ref = []
        self.pivot_local_nets = []
        self.sheets_to_clone = []
        self.pivot_bounding_box = None
        self.pivot_bounding_box_corners = ()

        self.polar_center = None

        self.minimum_radius = None
        self.minimum_angle = None

        self.minimum_width = None

        self.pivot_text = []
        self.pivot_tracks = []
        self.pivot_zones = []
        self.only_within_bbox = False
        self.pivot_sheet_level = 0

    def get_sheet_levels(self):
        return [i[0] for i in self.sheet_levels]

    def calculate_spacing(self, sheet_level):
        self.pivot_modules = []
        self.pivot_modules_id = []
        self.pivot_modules_ref = []
        self.pivot_local_nets = []
        self.sheets_to_clone = []
        self.pivot_bounding_box = None
        self.pivot_bounding_box_corners = ()

        self.polar_center = None

        self.minimum_radius = None
        self.minimum_angle = None

        self.minimum_width = None

        self.pivot_text = []
        self.pivot_tracks = []
        self.pivot_zones = []
        self.only_within_bbox = False
        self.pivot_sheet_level = 0

        # find out on which level one wants to clone
        for level in self.sheet_levels:
            if sheet_level == level[0]:
                self.pivot_sheet_level = self.sheet_levels.index(level)
                self.pivot_sheet_id = self.pivot_sheet_sel_id[0:self.pivot_sheet_level+1]

        # find all modules on the same sheet level
        for mod in self.modules:
            module_id = get_module_id(mod)
            sheet_id = get_sheet_id(mod)
            # if module is in the same hiearchical level or above
            if len(sheet_id) >= len(self.pivot_sheet_id):
                # and if its ID matches to the level we are replication
                if sheet_id[0:self.pivot_sheet_level+1] == self.pivot_sheet_id[0:self.pivot_sheet_level+1]:
                    self.pivot_modules.append(mod)
                    self.pivot_modules_id.append(module_id)
                    self.pivot_modules_ref.append(mod.GetReference())

        # find all local nets
        other_modules = []
        other_modules_ref = []
        # firstly find all other modules
        for mod in self.modules:
            if mod.GetReference() not in self.pivot_modules_ref:
                other_modules.append(mod)
                other_modules_ref.append(mod.GetReference())
        # then get nets other modules are connected to
        other_nets = self.get_nets_from_modules(other_modules)
        # then get nets only pivot modules are connected to
        pivot_nets = self.get_nets_from_modules(self.pivot_modules)

        for net in pivot_nets:
            if net not in other_nets:
                self.pivot_local_nets.append(net)

        # find all sheets to replicate
        # get all the sheets all the modules are binded to
        for mod in self.modules:
            module_id = get_module_id(mod)
            sheet_id = get_sheet_id(mod)
            # if the module id mathches to any of pivod modules id and we have not yet added this sheet
            # then check if sheet id below pivot_sheet_level matches pivot_sheet_id and
            # sheet_id at pivot_sheet_level is different to pivot_sheet_id
            if (module_id == self.pivot_mod_id) \
                    and not any(sheet_id[0:self.pivot_sheet_level+1] in sheet for sheet in self.sheets_to_clone)\
                    and (sheet_id[0:self.pivot_sheet_level] == self.pivot_sheet_id[0:self.pivot_sheet_level])\
                    and (sheet_id[self.pivot_sheet_level] != self.pivot_sheet_id[self.pivot_sheet_level]):
                # Get the number in the reference.
                ref = [c for c in mod.GetReference() if c.isdigit()]
                if ref:
                    refnum = int(''.join(ref))
                else:
                    refnum = -1

                # Add the number and the sheet ID.
                self.sheets_to_clone.append((refnum, sheet_id[0:self.pivot_sheet_level+1]))

        # Sort by the number of the replicated modules, and then discard
        # these numbers.
        self.sheets_to_clone = [s for r, s in sorted(self.sheets_to_clone)]

        # get bounding bounding box of all pivot modules
        bounding_box = self.pivot_mod.GetFootprintRect()
        top = bounding_box.GetTop()
        bottom = bounding_box.GetBottom()
        left = bounding_box.GetLeft()
        right = bounding_box.GetRight()
        for mod in self.pivot_modules:
            mod_box = mod.GetFootprintRect()
            top = min(top, mod_box.GetTop())
            bottom = max(bottom, mod_box.GetBottom())
            left = min(left, mod_box.GetLeft())
            right = max(right, mod_box.GetRight())

        position = pcbnew.wxPoint(left, top)
        size = pcbnew.wxSize(right - left, bottom - top)
        self.pivot_bounding_box = pcbnew.EDA_RECT(position, size)

        # get corner points for the pivot bunding box - might need them for proper rotated bounding box
        #
        top_left = (self.pivot_bounding_box.GetLeft(), self.pivot_bounding_box.GetTop())
        top_right = (self.pivot_bounding_box.GetRight(), self.pivot_bounding_box.GetTop())
        bottom_right = (self.pivot_bounding_box.GetRight(), self.pivot_bounding_box.GetBottom())
        bottom_left = (self.pivot_bounding_box.GetLeft(), self.pivot_bounding_box.GetBottom())
        self.pivot_bounding_box_corners = (top_left, top_right, bottom_right, bottom_left)

        # get radius for polar replication
        middle = (right + left)/2
        self.polar_center = (middle, bottom)

        # get minimal radius - used by GUI to autofill in case of polar replication
        # could be improved with proper formulae, this is just a rough estimae
        number_of_all_sheets = 1 + len(self.sheets_to_clone)
        width_of_sheet = (right - left) / SCALE
        circumference = number_of_all_sheets * width_of_sheet
        self.minimum_radius = circumference / (2 * math.pi)
        self.minimum_angle = 360.0 / number_of_all_sheets

        # get minimal width - GUI assumes horizontal replication
        self.minimum_width = (right - left) / SCALE
        pass

    def prepare_for_replication(self, only_within_boundingbox):
        self.only_within_bbox = only_within_boundingbox
        # find all tracks within the pivot bounding box
        all_tracks = self.board.GetTracks()
        # keep only tracks that are within our bounding box

        # get all the tracks for replication
        for track in all_tracks:
            track_bb = track.GetBoundingBox()
            # if track is contained or intersecting the bounding box
            if (only_within_boundingbox and self.pivot_bounding_box.Contains(track_bb)) or\
               (not only_within_boundingbox and self.pivot_bounding_box.Intersects(track_bb)):
                self.pivot_tracks.append(track)
            # even if track is not within the bounding box
            else:
                # check if it on a local net
                if track.GetNetname() in self.pivot_local_nets:
                    # and add it to the
                    self.pivot_tracks.append(track)

        # get all zones in pivot bounding box
        all_zones = []
        for zoneid in range(self.board.GetAreaCount()):
            all_zones.append(self.board.GetArea(zoneid))
        # find all zones which are completely within the pivot bounding box
        for zone in all_zones:
            zone_bb = zone.GetBoundingBox()
            if (only_within_boundingbox and self.pivot_bounding_box.Contains(zone_bb)) or\
               (not only_within_boundingbox and self.pivot_bounding_box.Intersects(zone_bb)):
                self.pivot_zones.append(zone)

        # get all text objects in pivot bounding box
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.TEXTE_PCB):
                continue
            text_bb = drawing.GetBoundingBox()
            if only_within_boundingbox:
                if self.pivot_bounding_box.Contains(text_bb):
                    self.pivot_text.append(drawing)
            else:
                if self.pivot_bounding_box.Intersects(text_bb):
                    self.pivot_text.append(drawing)

    def extract_subsheets(self, filename):
        with open(filename) as f:
            file_folder = os.path.dirname(os.path.abspath(filename))
            file_lines = f.read()
        # alternative solution
        # extract all sheet references
        sheet_indices = [m.start() for m in re.finditer('\$Sheet', file_lines)]
        endsheet_indices = [m.start() for m in re.finditer('\$EndSheet', file_lines)]

        if len(sheet_indices) != len(endsheet_indices):
            raise LookupError("Schematic page contains errors")

        sheet_locations = zip(sheet_indices, endsheet_indices)
        for sheet_location in sheet_locations:
            sheet_reference = file_lines[sheet_location[0]:sheet_location[1]].split('\n')
            # parse the sheed description
            for line in sheet_reference:
                # found sheet ID
                if line.startswith('U '):
                    subsheet_id = line.split()[1]
                # found sheet filename
                if line.startswith('F1 '):
                    subsheet_path = line.split()[1].rstrip("\"").lstrip("\"")
                    subsheet_line = file_lines.split("\n").index(line)
                    if not os.path.isabs(subsheet_path):
                        # check if path is encoded with variables
                        if "${" in subsheet_path:
                            start_index = subsheet_path.find("${") + 2
                            end_index = subsheet_path.find("}")
                            env_var = subsheet_path[start_index:end_index]
                            path = os.getenv(env_var)
                            # if variable is not defined rasie an exception
                            if path is None:
                                raise LookupError("Can not find subsheet: " + subsheet_path)
                            # replace variable with full path
                            subsheet_path = subsheet_path.replace("${", "") \
                                .replace("}", "") \
                                .replace("env_var", path)

                    # if path is still not absolute, then it is relative to project
                    if not os.path.isabs(subsheet_path):
                        subsheet_path = os.path.join(file_folder, subsheet_path)

                    subsheet_path = os.path.normpath(subsheet_path)
                    # found subsheet reference go for the next one, no need to parse further
                    break

            file_path = os.path.abspath(subsheet_path)
            rel_subsheet_path = os.path.relpath(file_path, self.project_path)

            yield rel_subsheet_path, subsheet_line, subsheet_id

    def find_all_sch_files(self, filename, list_of_files):
        for sheet, line_nr, sheet_id in self.extract_subsheets(filename):
            list_of_files.append((sheet, sheet_id))
            list_of_files = self.find_all_sch_files(sheet, list_of_files)
        return list_of_files

    @staticmethod
    def get_nets_from_modules(modules):
        # go through all modules and their pads and get the nets they are connected to
        nets = []
        for mod in modules:
            # get their pads
            pads = mod.PadsList()
            # get net
            for pad in pads:
                nets.append(pad.GetNetname())

        # remove duplicates
        nets_clean = []
        for i in nets:
            if i not in nets_clean:
                nets_clean.append(i)
        return nets_clean

    def get_nets_on_sheet(self, sheet_id):
        # find all modules, pads and nets on this sheet
        sheet_modules = []
        for mod in self.modules:
            mod_sheet_id = get_sheet_id(mod)
            if mod_sheet_id == sheet_id:
                sheet_modules.append(mod)
        # go through all modules and their pads and get the nets they are connected to
        nets_clean = self.get_nets_from_modules(sheet_modules)
        return nets_clean

    def get_net_pairs(self, sheet_id):
        """ find all net pairs between pivot sheet and current sheet"""
        # find all modules, pads and nets on this sheet
        sheet_modules = []
        sheet_modules_ref = []
        for mod in self.modules:
            mod_sheet_id = get_sheet_id(mod)
            # if on the same level
            if len(sheet_id) == len(mod_sheet_id):
                if mod_sheet_id == sheet_id:
                    sheet_modules.append(mod)
                    sheet_modules_ref.append(mod.GetReference())
            else:
                if len(sheet_id) < len(mod_sheet_id)\
                        and len(set(sheet_id) & set(mod_sheet_id)) == len(sheet_id):
                    sheet_modules.append(mod)
                    sheet_modules_ref.append(mod.GetReference())
        # find all net pairs via same modules pads,
        net_pairs = []
        net_dict = {}
        # construct module pairs
        mod_matches = []
        for p_mod in self.pivot_modules:
            p_mod_id = get_module_id(p_mod)
            p_sheet_id = get_sheet_id(p_mod)
            mod_matches.append([p_mod, p_mod_id, p_sheet_id])

        for s_mod in sheet_modules:
            s_mod_id = get_module_id(s_mod)
            s_sheet_id = get_sheet_id(s_mod)
            for mod in mod_matches:
                if mod[1] == s_mod_id:
                    index = mod_matches.index(mod)
                    mod_matches[index].append(s_mod)
                    mod_matches[index].append(s_mod_id)
                    mod_matches[index].append(s_sheet_id)
        # find closest match
        mod_pairs = []
        mod_pairs_by_reference = []
        for mod in mod_matches:
            index = mod_matches.index(mod)
            matches = (len(mod) - 3) / 3
            if matches != 1:
                match_len = []
                for index in range(0, matches):
                    match_len.append(len(set(mod[2]) & set(mod[2+3*(index+1)])))
                index = match_len.index(max(match_len))
                mod_pairs.append((mod[0], mod[3*(index+1)]))
                mod_pairs_by_reference.append((mod[0].GetReference(), mod[3*(index+1)].GetReference()))
            elif matches == 1:
                mod_pairs.append((mod[0], mod[3]))
                mod_pairs_by_reference.append((mod[0].GetReference(), mod[3].GetReference()))

        pad_pairs = []
        for x in range(len(mod_pairs)):
            pad_pairs.append([])

        for pair in mod_pairs:
            index = mod_pairs.index(pair)
            # get all footprint pads
            p_mod_pads = pair[0].PadsList()
            s_mod_pads = pair[1].PadsList()
            # create a list of padsnames and pads
            p_pads = []
            s_pads = []
            for pad in p_mod_pads:
                p_pads.append((pad.GetName(), pad))
            for pad in s_mod_pads:
                s_pads.append((pad.GetName(), pad))
            # sort by padnames
            p_pads.sort(key=lambda tup: tup[0])
            s_pads.sort(key=lambda tup: tup[0])
            # extract pads and append them to pad pairs list
            pad_pairs[index].append([x[1] for x in p_pads])
            pad_pairs[index].append([x[1] for x in s_pads])

        for pair in mod_pairs:
            index = mod_pairs.index(pair)
            p_mod = pair[0]
            s_mod = pair[1]
            # get their pads
            p_mod_pads = pad_pairs[index][0]
            s_mod_pads = pad_pairs[index][1]
            # I am going to assume pads are in the same order
            p_nets = []
            s_nets = []
            # get nelists for each pad
            for p_pad in p_mod_pads:
                pad_name = p_pad.GetName()
                p_nets.append((pad_name, p_pad.GetNetname()))
            for s_pad in s_mod_pads:
                pad_name = s_pad.GetName()
                s_nets.append((pad_name, s_pad.GetNetname()))
                net_dict[s_pad.GetNetname()] = s_pad.GetNet()
            # sort both lists by pad name
            # so that they have the same order - needed in some cases
            # as the iterator thorugh the pads list does not return pads always in the proper order
            p_nets.sort(key=lambda tup: tup[0])
            s_nets.sort(key=lambda tup: tup[0])
            # build list of net tupules
            for net in p_nets:
                index = get_index_of_tuple(p_nets, 1, net[1])
                net_pairs.append((p_nets[index][1], s_nets[index][1]))

        # remove duplicates
        net_pairs_clean = list(set(net_pairs))

        return net_pairs_clean, net_dict

    def remove_zones_tracks(self):
        for sheet in self.sheets_to_clone:
            # get modules on a sheet
            mod_sheet = []
            for mod in self.modules:
                sheet_id = get_sheet_id(mod)
                # if module is on selected sheet
                if sheet_id == sheet:
                    mod_sheet.append(mod)
            # get bounding box
            bounding_box = get_bounding_box_of_modules(mod_sheet)

            tracks_to_remove = []
            # from all the tracks on board
            all_tracks = self.board.GetTracks()
            # remove the tracks that are not on nets contained in this sheet
            nets_on_sheet = self.get_nets_on_sheet(sheet)
            tracks_on_nets_on_sheet = []
            for track in all_tracks:
                if track.GetNetname() in nets_on_sheet:
                    tracks_on_nets_on_sheet.append(track)

            for track in tracks_on_nets_on_sheet:
                # minus the tracks in pivot bounding box
                if track not in self.pivot_tracks:
                    track_in_bounding_box = track.GetBoundingBox()
                    # add the tracks containing/interesecting in the replicated bounding box
                    # on the list for removal
                    if self.only_within_bbox:
                        if bounding_box.Contains(track_in_bounding_box):
                            tracks_to_remove.append(track)
                    else:
                        if bounding_box.Intersects(track_in_bounding_box):
                            tracks_to_remove.append(track)
            # remove tracks
            for track in tracks_to_remove:
                self.board.RemoveNative(track)

            zones_to_remove = []
            # from all the zones on the board
            all_zones = []
            for zoneid in range(self.board.GetAreaCount()):
                all_zones.append(self.board.GetArea(zoneid))
            # remove the zones that are not on nets contained in this sheet
            zones_on_nets_on_sheet = []
            for zone in all_zones:
                if zone.GetNetname() in nets_on_sheet:
                    zones_on_nets_on_sheet.append(zone)
            for zone in all_zones:
                # minus the zones in pivot bounding box
                if zone not in self.pivot_zones:
                    zone_in_bounding_box = zone.GetBoundingBox()
                    # add the zones containing/interesecting in the replicated bounding box
                    # on the list for removal
                    if self.only_within_bbox:
                        if bounding_box.Contains(zone_in_bounding_box):
                            zones_to_remove.append(zone)
                    else:
                        if bounding_box.Intersects(zone_in_bounding_box):
                            zones_to_remove.append(zone)
            # remove tracks
            for zone in zones_to_remove:
                self.board.RemoveNative(zone)

            text_to_remove = []
            # from all text items on the board
            for drawing in self.board.GetDrawings():
                if not isinstance(drawing, pcbnew.TEXTE_PCB):
                    continue
                # ignore text in the pivot sheet
                if drawing in self.pivot_text:
                    continue

                # add text in/intersecting with the replicated bounding box to
                # the list for removal.
                text_bb = drawing.GetBoundingBox()
                if self.only_within_bbox:
                    if bounding_box.Contains(text_bb):
                        text_to_remove.append(drawing)
                else:
                    if bounding_box.Intersects(text_bb):
                        text_to_remove.append(drawing)

            # remove text objects
            for text in text_to_remove:
                self.board.RemoveNative(text)

    def replicate_modules(self, x_offset, y_offset, polar):
        global SCALE
        """ method which replicates modules"""
        for sheet in self.sheets_to_clone:
            sheet_index = self.sheets_to_clone.index(sheet) + 1
            # begin with modules
            for mod in self.modules:
                module_id = get_module_id(mod)
                sheet_id = get_sheet_id(mod)
                # if module is on selected sheet or higher
                a = sheet_id[0:self.pivot_sheet_level+1]
                b = sheet[0:self.pivot_sheet_level+1]
                if a == b:
                    # find which is the corresponding pivot module
                    if module_id in self.pivot_modules_id:
                        # get coresponding pivot module and its position
                        # find the best match
                        mod_locations = [index for index, pivot_module in enumerate(self.pivot_modules_id) if pivot_module == module_id]
                        if len(mod_locations) > 1:
                            max_matches = -1
                            for loc in mod_locations:
                                mod_ref = mod.GetReference()
                                pivot_mod_ref = self.pivot_modules[loc].GetReference()
                                pivot_mod_path = get_sheet_id(self.pivot_modules[loc])
                                mod_path = sheet_id
                                matches = len(set(mod_path) & set(pivot_mod_path))
                                if matches > max_matches:
                                    max_matches = matches
                                    index = loc
                        else:
                            index = mod_locations[0]

                        # index = self.pivot_modules_id.index(module_id)
                        mod_to_clone = self.pivot_modules[index]
                        pivot_mod_position = mod_to_clone.GetPosition()
                        pivot_mod_orientation = mod_to_clone.GetOrientationDegrees()
                        pivot_mod_flipped = mod_to_clone.IsFlipped()

                        if polar:
                            # get the pivot point
                            pivot_point = (self.polar_center[0], self.polar_center[1] + x_offset * SCALE)
                            newposition = rotate_around_pivot_point(pivot_mod_position, pivot_point, sheet_index * y_offset)
                        else:
                            # get new position - cartesian
                            newposition = (pivot_mod_position[0] + sheet_index * x_offset * SCALE,
                                           pivot_mod_position[1] + sheet_index * y_offset * SCALE)

                        # convert to tuple of integers
                        newposition = [int(x) for x in newposition]
                        # place current module
                        mod.SetPosition(pcbnew.wxPoint(*newposition))

                        if (mod.IsFlipped() and not pivot_mod_flipped) or (pivot_mod_flipped and not mod.IsFlipped()):
                            mod.Flip(mod.GetPosition())

                        # set module orientation
                        if polar:
                            new_orientation = pivot_mod_orientation - sheet_index * y_offset
                            # check for orientation wraparound
                            if new_orientation > 360.0:
                                new_orientation = new_orientation - 360
                            if new_orientation < 0.0:
                                new_orientation = new_orientation + 360
                        else:
                            new_orientation = pivot_mod_orientation
                        mod.SetOrientationDegrees(new_orientation)

                        # Copy local settings.
                        mod.SetLocalClearance(mod_to_clone.GetLocalClearance())
                        mod.SetLocalSolderMaskMargin(mod_to_clone.GetLocalSolderMaskMargin())
                        mod.SetLocalSolderPasteMargin(mod_to_clone.GetLocalSolderPasteMargin())
                        mod.SetLocalSolderPasteMarginRatio(mod_to_clone.GetLocalSolderPasteMarginRatio())
                        mod.SetZoneConnection(mod_to_clone.GetZoneConnection())

                        # replicate also text layout
                        # get pivot_module_text
                        # get module text
                        pivot_mod_text_items = get_module_text_items(mod_to_clone)
                        mod_text_items = get_module_text_items(mod)
                        # replicate each text item
                        for pivot_text in pivot_mod_text_items:
                            index = pivot_mod_text_items.index(pivot_text)
                            pivot_text_position = pivot_text.GetPosition()
                            if polar:
                                pivot_point = (self.polar_center[0], self.polar_center[1] + x_offset * SCALE)
                                newposition = rotate_around_pivot_point(pivot_text_position, pivot_point, sheet_index * y_offset)
                            else:
                                newposition = (pivot_text_position[0] + sheet_index * x_offset * SCALE,
                                               pivot_text_position[1] + sheet_index * y_offset * SCALE)

                            # convert to tuple of integers
                            newposition = [int(x) for x in newposition]
                            mod_text_items[index].SetPosition(pcbnew.wxPoint(*newposition))

                            # set orientation
                            mod_text_items[index].SetTextAngle(pivot_text.GetTextAngle())

                            # set visibility
                            mod_text_items[index].SetVisible(pivot_text.IsVisible())

    def replicate_text(self, x_offset, y_offset, polar):
        global SCALE
        # start cloning
        for sheet_index, sheet in enumerate(self.sheets_to_clone, 1):
            for text in self.pivot_text:
                pivot_position = text.GetPosition()
                pivot_angle = text.GetTextAngle() / 10   # Returned in deci-degrees.
                newtext = text.Duplicate()

                # Calculate new position.
                if polar:
                    pivot_point = (self.polar_center[0], self.polar_center[1] + x_offset * SCALE)
                    newposition = rotate_around_pivot_point(pivot_position, pivot_point, sheet_index * y_offset)

                    # Calculate new angle.
                    new_angle = pivot_angle - sheet_index * y_offset
                    if new_angle > 360.0:
                        new_angle = new_angle - 360
                    if new_angle < 0.0:
                        new_angle = new_angle + 360
                    newtext.SetTextAngle(new_angle * 10)  # Set in deci-degrees.
                else:
                    newposition = (pivot_position[0] + sheet_index * x_offset * SCALE,
                                   pivot_position[1] + sheet_index * y_offset * SCALE)

                # Update position and add to board.
                newposition = [int(x) for x in newposition]
                newtext.SetPosition(pcbnew.wxPoint(*newposition))
                self.board.Add(newtext)

    def replicate_tracks(self, x_offset, y_offset, polar):
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
                tup = [item for item in net_pairs if item[0] == from_net_name]
                # if net was not fount, then the track is not part of this sheet and should not be cloned
                if not tup:
                    pass
                else:
                    to_net_name = tup[0][1]
                    to_net = net_dict[to_net_name]

                    # finally make a copy
                    # this came from Miles Mccoo, I only extended it with polar support
                    # https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
                    if track.GetClass() == "VIA":
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
                        if polar:
                            # get the pivot point
                            pivot_point = (self.polar_center[0], self.polar_center[1] + x_offset * SCALE)

                            newposition = rotate_around_pivot_point((track.GetPosition().x, track.GetPosition().y),
                                                                    pivot_point, sheet_index * y_offset)
                        else:
                            newposition = (track.GetPosition().x + sheet_index*x_offset*SCALE,
                                           track.GetPosition().y + sheet_index*y_offset*SCALE)

                        # convert to tuple of integers
                        newposition = [int(x) for x in newposition]

                        newvia.SetPosition(pcbnew.wxPoint(*newposition))

                        newvia.SetViaType(track.GetViaType())
                        newvia.SetWidth(track.GetWidth())
                        newvia.SetDrill(track.GetDrill())
                        newvia.SetNet(to_net)
                    else:
                        newtrack = pcbnew.TRACK(self.board)
                        # need to add before SetNet will work, so just doing it first
                        self.board.Add(newtrack)
                        if polar:
                            # get the pivot point
                            pivot_point = (self.polar_center[0], self.polar_center[1] + x_offset * SCALE)
                            newposition = rotate_around_pivot_point((track.GetStart().x, track.GetStart().y),
                                                                    pivot_point, sheet_index * y_offset)
                            # convert to tuple of integers
                            newposition = [int(x) for x in newposition]
                            newtrack.SetStart(pcbnew.wxPoint(*newposition))

                            newposition = rotate_around_pivot_point((track.GetEnd().x, track.GetEnd().y),
                                                                    pivot_point, sheet_index * y_offset)
                            # convert to tuple of integers
                            newposition = [int(x) for x in newposition]
                            newtrack.SetEnd(pcbnew.wxPoint(*newposition))
                        else:
                            newtrack.SetStart(pcbnew.wxPoint(track.GetStart().x + sheet_index*x_offset*SCALE,
                                                             track.GetStart().y + sheet_index*y_offset*SCALE))
                            newtrack.SetEnd(pcbnew.wxPoint(track.GetEnd().x + sheet_index*x_offset*SCALE,
                                                           track.GetEnd().y + sheet_index*y_offset*SCALE))
                        newtrack.SetWidth(track.GetWidth())
                        newtrack.SetLayer(track.GetLayer())

                        newtrack.SetNet(to_net)

    def replicate_zones(self, x_offset, y_offset, polar):
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
                # if zone is not on copper layer it does not matter on which net it is
                if not zone.IsOnCopperLayer():
                    tup = [('', '')]
                else:
                    tup = [item for item in net_pairs if item[0] == from_net_name]

                # there is no net
                if not tup:
                    # Allow keepout zones to be cloned.
                    if zone.GetIsKeepout():
                        tup = [('', '')]
                    # do not clone
                    else:
                        continue

                # start the clone
                to_net_name = tup[0][1]
                if to_net_name == u'':
                    to_net = 0
                else:
                    to_net = net_dict[to_net_name].GetNet()

                # now I can finally make a copy of a zone
                # this came partially from Miles Mccoo. I only extended it with polar support
                # https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
                coords = get_coordinate_points_of_shape_poly_set(zone.Outline())
                if polar:
                    pivot_point = (self.polar_center[0], self.polar_center[1] + x_offset * SCALE)
                    newposition = rotate_around_pivot_point((coords[0][0], coords[0][1]), pivot_point, sheet_index * y_offset)
                    newposition = [int(x) for x in newposition]
                    newzone = self.board.InsertArea(to_net,
                                                    0,
                                                    zone.GetLayer(),
                                                    newposition[0],
                                                    newposition[1],
                                                    pcbnew.CPolyLine.DIAGONAL_EDGE)
                    newoutline = newzone.Outline()
                    for pt in coords[1:]:
                        newposition = rotate_around_pivot_point((pt[0], pt[1]), pivot_point,
                                                                sheet_index * y_offset)
                        newposition = [int(x) for x in newposition]
                        newoutline.Append(newposition[0], newposition[1])
                else:
                    newposition = (coords[0][0] + sheet_index * x_offset * SCALE,
                                   coords[0][1] + sheet_index * y_offset * SCALE)
                    newposition = [int(x) for x in newposition]
                    newzone = self.board.InsertArea(to_net,
                                                    0,
                                                    zone.GetLayer(),
                                                    newposition[0],
                                                    newposition[1],
                                                    pcbnew.CPolyLine.DIAGONAL_EDGE)
                    newoutline = newzone.Outline()
                    for pt in coords[1:]:
                        newoutline.Append(pt[0] + int(sheet_index*x_offset*SCALE),
                                          pt[1] + int(sheet_index*y_offset*SCALE))

                # copy zone settings
                newzone.SetPriority(zone.GetPriority())
                newzone.SetLayerSet(zone.GetLayerSet())
                newzone.SetFillMode(zone.GetFillMode())
                newzone.SetThermalReliefGap(zone.GetThermalReliefGap())
                newzone.SetThermalReliefCopperBridge(zone.GetThermalReliefCopperBridge())
                newzone.SetIsFilled(zone.IsFilled())
                newzone.SetZoneClearance(zone.GetZoneClearance())
                newzone.SetPadConnection(zone.GetPadConnection())
                newzone.SetMinThickness(zone.GetMinThickness())

                # Copy the keepout properties.
                if zone.GetIsKeepout():
                    newzone.SetIsKeepout(True)
                    newzone.SetLayerSet(zone.GetLayerSet())
                    newzone.SetDoNotAllowCopperPour(zone.GetDoNotAllowCopperPour())
                    newzone.SetDoNotAllowTracks(zone.GetDoNotAllowTracks())
                    newzone.SetDoNotAllowVias(zone.GetDoNotAllowVias())
                pass

    def replicate_layout(self, x_offset, y_offset,
                         replicate_containing_only,
                         remove_existing_nets_zones,
                         replicate_tracks,
                         replicate_zones,
                         replicate_text,
                         polar):
        self.prepare_for_replication(replicate_containing_only)
        if remove_existing_nets_zones:
            self.remove_zones_tracks()
        self.replicate_modules(x_offset, y_offset, polar)
        if remove_existing_nets_zones:
            self.remove_zones_tracks()
        if replicate_tracks:
            self.replicate_tracks(x_offset, y_offset, polar)
        if replicate_zones:
            self.replicate_zones(x_offset, y_offset, polar)
        if replicate_text:
            self.replicate_text(x_offset, y_offset, polar)


def test_multiple_inner(x, y, within, polar):
    board = pcbnew.LoadBoard('multiple_hierarchy.kicad_pcb')
    replicator = Replicator(board=board, pivot_module_reference='Q301')
    # get sheet levels
    sheet_levels = replicator.get_sheet_levels()
    # select which level to replicate
    replicator.calculate_spacing(sheet_levels[-1])
    replicator.calculate_spacing(sheet_levels[0])
    replicator.calculate_spacing(sheet_levels[-1])

    replicator.replicate_layout(x, y,
                                replicate_containing_only=within,
                                remove_existing_nets_zones=True,
                                replicate_tracks=True,
                                replicate_zones=True,
                                replicate_text=True,
                                polar=polar)

    # save the board
    filename = 'multiple_hierarchy_top.kicad_pcb'
    saved = pcbnew.SaveBoard(filename, board)

    # compare files
    import difflib
    errnum = 0
    with open('test_'+filename, 'r') as correct_board:
        with open(filename, 'r') as tested_board:
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
            if ((('version' in diffstring[index + 1]) and ('version' in diffstring[index + 2])) or
                (('tstamp' in diffstring[index + 1]) and ('tstamp' in diffstring[index + 2]))):
                # this is not a problem
                pass
            else:
                # this is a problem
                errnum = errnum + 1
    return errnum


def test_multiple_outer(x, y, within, polar):
    board = pcbnew.LoadBoard('multiple_hierarchy_top_done.kicad_pcb')
    replicator = Replicator(board=board, pivot_module_reference='Q301') # J201 ali Q301
    # get sheet levels
    sheet_levels = replicator.get_sheet_levels()
    # select which level to replicate
    replicator.calculate_spacing(sheet_levels[0])

    replicator.replicate_layout(x, y,
                                replicate_containing_only=within,
                                remove_existing_nets_zones=True,
                                replicate_tracks=True,
                                replicate_zones=True,
                                replicate_text=True,
                                polar=polar)

    # save the board
    filename = 'multiple_hierarchy_base.kicad_pcb'
    saved = pcbnew.SaveBoard(filename, board)

    # compare files
    import difflib
    errnum = 0
    with open('test_'+filename, 'r') as correct_board:
        with open(filename, 'r') as tested_board:
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
            if ((('version' in diffstring[index + 1]) and ('version' in diffstring[index + 2])) or
                (('tstamp' in diffstring[index + 1]) and ('tstamp' in diffstring[index + 2]))):
                # this is not a problem
                pass
            else:
                # this is a problem
                errnum = errnum + 1
    return errnum


def test_replicate(x, y, within, polar):
    import difflib

    filename = ''
    if within is True and polar is False:
        filename = 'test_board_only_within.kicad_pcb'
    if within is False and polar is False:
        filename = 'test_board_all.kicad_pcb'
    if within is False and polar is True:
        filename = 'test_board_polar.kicad_pcb'

    # load test board
    board = pcbnew.LoadBoard('test_board.kicad_pcb')
    # run the replicator
    replicator = Replicator(board=board, pivot_module_reference='Q2002')
    sheet_levels = replicator.get_sheet_levels()
    # select which level to replicate
    replicator.calculate_spacing(sheet_levels[0])
    replicator.replicate_layout(x, y,
                                replicate_containing_only=within,
                                remove_existing_nets_zones=True,
                                replicate_tracks=True,
                                replicate_zones=True,
                                replicate_text=True,
                                polar=polar)
    # save the board
    saved = pcbnew.SaveBoard('temp_'+filename, board)

    # compare files
    errnum = 0
    with open('temp_'+filename, 'r') as tested_board:
        with open(filename, 'r') as correct_board:
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
            if ((('version' in diffstring[index + 1]) and ('version' in diffstring[index + 2])) or
                (('tstamp' in diffstring[index + 1]) and ('tstamp' in diffstring[index + 2]))):
                # this is not a problem
                pass
            else:
                # this is a problem
                errnum = errnum + 1
    return errnum


def main():
    errnum_within = 0
    errnum_all = 0
    errnum_polar = 0
    errnum_multiple_inner = 0
    errnum_multiple_outer = 0

    errnum_within = test_replicate(25.0, 0.0, within=True, polar=False)
    errnum_all = test_replicate(25.0, 0.0, within=False, polar=False)
    errnum_polar = test_replicate(20, 60, within=False, polar=True)

    os.chdir("D:/Mitja/Plate/Kicad_libs/action_plugins/replicate_layout/multiple_hierarchy")
    errnum_multiple_inner = test_multiple_inner(25, 0.0, within=False, polar=False)
    errnum_multiple_outer = test_multiple_outer(50, 0.0, within=False, polar=False)

    if errnum_all == 0\
       and errnum_within == 0\
       and errnum_all == 0\
       and errnum_polar == 0\
       and errnum_multiple_inner == 0\
       and errnum_multiple_outer == 0:
        print "passed all tests"

    if errnum_within != 0:
        print "failed replicating only containing"
    if errnum_all != 0:
        print "failed replicating complete (with intersections)"
    if errnum_polar != 0:
        print "failed replicating polar"
    if errnum_multiple_inner != 0:
        print "failed replicating multiple inner"
    if errnum_multiple_outer != 0:
        print "failed replicating multiple outer"


# for testing purposes only
if __name__ == "__main__":
    main()
