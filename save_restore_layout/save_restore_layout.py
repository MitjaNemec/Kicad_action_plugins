# -*- coding: utf-8 -*-
#  save_restore_layout.py
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
import re
import hashlib
import pickle
import math
import tempfile

Module = namedtuple('Module', ['ref', 'mod', 'mod_id', 'sheet_id', 'filename'])

LayoutData = namedtuple('LayoutData', ['layout', 'hash', 'dict_of_sheets', 'list_of_local_nets', 'level', 'level_filename'])

logger = logging.getLogger(__name__)

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename, 'rb') as f:
    # read and decode
    version_file_contents = f.read().decode('utf-8')
    # extract first line
    VERSION = version_file_contents.split('\n')[0].strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


# V5.1.x and 5.99 compatibility layer
def get_path(module):
    path = module.GetPath()
    if hasattr(path, 'AsString'):
        path_raw = path.AsString()
        path = "/".join(map(lambda x: x[-8:].upper(), path_raw.split('/')))
    return path

# V5.99 forward compatibility
def flip_module(module, position):
    if module.Flip.__doc__ == "Flip(MODULE self, wxPoint aCentre, bool aFlipLeftRight)":
        module.Flip(position, False)
    else:
        module.Flip(position)


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
    list_of_items = [module.mod.Reference(), module.mod.Value()]

    module_items = module.mod.GraphicalItems()
    for item in module_items:
        if type(item) is pcbnew.TEXTE_MODULE:
            list_of_items.append(item)
    return list_of_items


class Footprint():
    def __init__(self, ref, mod, mod_id, sheet_id, sheetname=None, filename=None):
        self.ref = ref
        self.mod = mod
        self.mod_id = mod_id
        self.sheet_id = sheet_id
        self.sheetname = sheetname
        self.filename = filename


class SchData():
    @staticmethod
    def extract_subsheets(filename):
        with open(filename, 'rb') as f:
            file_folder = os.path.dirname(os.path.abspath(filename))
            file_lines = f.read().decode('utf-8')
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
                # found sheet name
                if line.startswith('F0 '):
                    partial_line = line.lstrip("F0 ")
                    partial_line = " ".join(partial_line.split()[:-1])
                    # remove the last field (text size)
                    subsheet_name = partial_line.rstrip("\"").lstrip("\"")
                # found sheet filename
                if line.startswith('F1 '):
                    subsheet_path = re.findall("\s\"(.*.sch)\"\s", line)[0]
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
            yield file_path, subsheet_id, subsheet_name

    def find_all_sch_files(self, filename, dict_of_sheets):
        for file_path, subsheet_id, subsheet_name in self.extract_subsheets(filename):
            dict_of_sheets[subsheet_id] = [subsheet_name, file_path]
            dict_of_sheets = self.find_all_sch_files(file_path, dict_of_sheets)
        return dict_of_sheets

    def __init__(self, board):
        main_sch_file = os.path.abspath(board.GetFileName()).replace(".kicad_pcb", ".sch")
        self.project_folder = os.path.dirname(main_sch_file)
        # get relation between sheetname and it's id
        logger.info('getting project hierarchy from schematics')
        self.dict_of_sheets = self.find_all_sch_files(main_sch_file, {})
        logger.info("Project hierarchy looks like:\n%s" % repr(self.dict_of_sheets))

        # make all paths relative
        for x in self.dict_of_sheets.keys():
            path = self.dict_of_sheets[x][1]
            self.dict_of_sheets[x] = [self.dict_of_sheets[x][0], os.path.relpath(path, self.project_folder)]

    def get_sch_hash(self, sch_file, md5hash):
        # load sch file
        with open(sch_file, 'rb') as f:
            file_contents = f.read().decode('utf-8')
            sch_lines = file_contents.split('\n')

        # remove all lines containing references (L, U, AR) and other stuff
        sch_file_without_reference \
        = [line for line in sch_lines if (not line.startswith("L ")
                                          and not line.startswith("F0 ")
                                          and not line.startswith("F 0")
                                          and not line.startswith("AR ")
                                          and not line.startswith("Sheet")
                                          and not line.startswith("LIBS:")
                                          and not line.startswith("EELAYER"))]

        # caluclate the hash
        for line in sch_file_without_reference:
            md5hash.update(line.encode('utf-8'))

        return md5hash


class PcbData():
    @staticmethod
    def get_module_id(module):
        """ get module id """
        module_path = get_path(module).split('/')
        module_id = "/".join(module_path[-1:])
        return module_id

    @staticmethod
    def get_sheet_id(module):
        """ get sheet id """
        module_path = get_path(module)
        sheet_path = module_path.split('/')
        sheet_id = sheet_path[1:-1]
        return sheet_id

    def get_mod_by_ref(self, ref):
        for m in self.modules:
            if m.ref == ref:
                return m
        return None

    def get_board_modules(self, board):
        bmod = board.GetModules()
        modules = []
        mod_dict = {}
        for module in bmod:
            mod_named_tuple = Footprint(mod=module,
                                        mod_id=self.get_module_id(module),
                                        sheet_id=self.get_sheet_id(module),
                                        ref=module.GetReference())
            mod_dict[module.GetReference()] = mod_named_tuple
            modules.append(mod_named_tuple)

        return modules

    def set_modules_hierarchy_names(self, dict_of_sheets):
        for mod in self.modules:
            mod.sheetname = [dict_of_sheets[x][0] for x in mod.sheet_id]
            mod.filename = [dict_of_sheets[x][1] for x in mod.sheet_id]

    def __init__(self, board):
        self.board = board
        # construct a list of modules with all pertinent data 
        logger.info('getting a list of all footprints on board') 
        self.modules = self.get_board_modules(board)

    def get_modules_on_sheet(self, level):
        modules_on_sheet = []
        level_depth = len(level)
        for mod in self.modules:
            if level == mod.sheetname[0:level_depth]:
                modules_on_sheet.append(mod)
        return modules_on_sheet

    def get_modules_not_on_sheet(self, level):
        modules_not_on_sheet = []
        level_depth = len(level)
        for mod in self.modules:
            if level != mod.sheetname[0:level_depth]:
                modules_not_on_sheet.append(mod)
        return modules_not_on_sheet

    @staticmethod
    def get_nets_from_modules(modules):
        # go through all modules and their pads and get the nets they are connected to
        nets = []
        for mod in modules:
            # get their pads
            pads = mod.mod.Pads()
            # get net
            for pad in pads:
                nets.append(pad.GetNetname())

        # remove duplicates
        nets_clean = []
        for i in nets:
            if i not in nets_clean:
                nets_clean.append(i)
        return nets_clean

    def get_local_nets(self, pivot_modules, other_modules):
        # then get nets other modules are connected to
        other_nets = self.get_nets_from_modules(other_modules)
        # then get nets only pivot modules are connected to
        pivot_nets = self.get_nets_from_modules(pivot_modules)

        pivot_local_nets = []
        for net in pivot_nets:
            if net not in other_nets:
                pivot_local_nets.append(net)

        return pivot_local_nets

    @staticmethod
    def get_modules_bounding_box(modules):
        # get the pivot bounding box
        bounding_box = modules[0].mod.GetFootprintRect()
        top = bounding_box.GetTop()
        bottom = bounding_box.GetBottom()
        left = bounding_box.GetLeft()
        right = bounding_box.GetRight()
        for mod in modules:
            mod_box = mod.mod.GetFootprintRect()
            top = min(top, mod_box.GetTop())
            bottom = max(bottom, mod_box.GetBottom())
            left = min(left, mod_box.GetLeft())
            right = max(right, mod_box.GetRight())

        position = pcbnew.wxPoint(left, top)
        size = pcbnew.wxSize(right - left, bottom - top)
        bounding_box = pcbnew.EDA_RECT(position, size)
        return bounding_box

    def get_tracks(self, bounding_box, local_nets, containing):
        # find all tracks within the pivot bounding box
        all_tracks = self.board.GetTracks()
        # keep only tracks that are within our bounding box
        tracks = []
        # get all the tracks for replication
        for track in all_tracks:
            track_bb = track.GetBoundingBox()
            # if track is contained or intersecting the bounding box
            if (containing and bounding_box.Contains(track_bb)) or\
               (not containing and bounding_box.Intersects(track_bb)):
                tracks.append(track)
            # even if track is not within the bounding box
            else:
                # check if it on a local net
                if track.GetNetname() in local_nets:
                    # and add it to the
                    tracks.append(track)
        return tracks

    def get_zones(self, bounding_box, containing):
        # get all zones in pivot bounding box
        all_zones = []
        for zoneid in range(self.board.GetAreaCount()):
            all_zones.append(self.board.GetArea(zoneid))
        # find all zones which are completely within the pivot bounding box
        zones = []
        for zone in all_zones:
            zone_bb = zone.GetBoundingBox()
            if (containing and bounding_box.Contains(zone_bb)) or\
               (not containing and bounding_box.Intersects(zone_bb)):
                zones.append(zone)
        return zones

    def get_text_items(self, bounding_box, containing):
        # get all text objects in pivot bounding box
        pivot_text = []
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.TEXTE_PCB):
                continue
            text_bb = drawing.GetBoundingBox()
            if containing:
                if bounding_box.Contains(text_bb):
                    pivot_text.append(drawing)
            else:
                if bounding_box.Intersects(text_bb):
                    pivot_text.append(drawing)
        return pivot_text

    def get_drawings(self, bounding_box, containing):
        # get all drawings in pivot bounding box
        pivot_drawings = []
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.DRAWSEGMENT):
                continue
            dwg_bb = drawing.GetBoundingBox()
            if containing:
                if bounding_box.Contains(dwg_bb):
                    pivot_drawings.append(drawing)
            else:
                if bounding_box.Intersects(dwg_bb):
                    pivot_drawings.append(drawing)
        return pivot_drawings


class RestoreLayout():
    def __init__(self, board):
        logger.info("Getting board info")
        self.board = board
        logger.info("Getting schematics info")
        self.schematics = SchData(board)
        logger.info("Getting layout info")
        self.layout = PcbData(board)
        logger.info("Updating layout info with schematics info")
        self.layout.set_modules_hierarchy_names(self.schematics.dict_of_sheets)

    def get_mod_by_ref(self, mod_ref):
        return self.layout.get_mod_by_ref(mod_ref)

    @staticmethod
    def get_index_of_tuple(list_of_tuples, index, value):
        for pos, t in enumerate(list_of_tuples):
            if t[index] == value:
                return pos

    def get_net_pairs(self, modules_sheet_1, modules_sheet_2):
        """ find all net pairs between pivot sheet and current sheet"""
        # find all modules, pads and nets on this sheet
        sheet_modules = modules_sheet_1
        # find all net pairs via same modules pads,
        net_pairs = []
        net_dict = {}
        # construct module pairs
        mod_matches = []
        for p_mod in modules_sheet_2:
            mod_matches.append([p_mod.mod, p_mod.mod_id, p_mod.sheet_id])

        for s_mod in sheet_modules:
            for mod in mod_matches:
                if mod[1] == s_mod.mod_id:
                    index = mod_matches.index(mod)
                    mod_matches[index].append(s_mod.mod)
                    mod_matches[index].append(s_mod.mod_id)
                    mod_matches[index].append(s_mod.sheet_id)
        # find closest match
        mod_pairs = []
        mod_pairs_by_reference = []
        for mod in mod_matches:
            index = mod_matches.index(mod)
            matches = (len(mod) - 3) // 3
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
            p_mod_pads = pair[0].Pads()
            s_mod_pads = pair[1].Pads()
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
                index = self.get_index_of_tuple(p_nets, 1, net[1])
                net_pairs.append((p_nets[index][1], s_nets[index][1]))

        # remove duplicates
        net_pairs_clean = list(set(net_pairs))

        return net_pairs_clean, net_dict

    def replicate_modules(self, pivot_anchor_mod, pivot_modules, anchor_mod, modules):
        logger.info("Replicating footprints")
        # get anchor angle with respect to pivot module
        anchor_angle = anchor_mod.mod.GetOrientationDegrees()
        # get exact anchor position
        anchor_pos = anchor_mod.mod.GetPosition()

        anchor_delta_angle = pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
        anchor_delta_pos = anchor_pos - pivot_anchor_mod.mod.GetPosition()

        # go through all modules
        for mod in modules:
            # find proper match in pivot modules
            mod_to_clone = None
            list_of_possible_pivot_modules = []
            for pmod in pivot_modules:
                if pmod.mod_id == mod.mod_id:
                    list_of_possible_pivot_modules.append(pmod)

            # if there is more than one possible anchor, select the correct one
            if len(list_of_possible_pivot_modules) == 1:
                mod_to_clone = list_of_possible_pivot_modules[0]
            else:
                list_of_matches = []
                for m in list_of_possible_pivot_modules:
                    index = list_of_possible_pivot_modules.index(m)
                    matches = 0
                    for item in mod.sheet_id:
                        if item in m.sheet_id:
                            matches = matches + 1
                    list_of_matches.append((index, matches))
                # todo select the one with most matches
                index, _ = max(list_of_matches, key=lambda item: item[1])
                mod_to_clone = list_of_possible_pivot_modules[index]

            # get module to clone position
            pivot_mod_orientation = mod_to_clone.mod.GetOrientationDegrees()
            pivot_mod_pos = mod_to_clone.mod.GetPosition()
            # get relative position with respect to pivot anchor
            pivot_anchor_pos = pivot_anchor_mod.mod.GetPosition()
            pivot_mod_delta_pos = pivot_mod_pos - pivot_anchor_pos

            # new orientation is simple
            new_orientation = pivot_mod_orientation - anchor_delta_angle
            old_position = pivot_mod_delta_pos + anchor_pos
            newposition = rotate_around_pivot_point(old_position, anchor_pos, anchor_delta_angle)

            # convert to tuple of integers
            newposition = [int(x) for x in newposition]
            # place current module - only if current module is not also the anchor
            if mod.ref != anchor_mod.ref:
                mod.mod.SetPosition(pcbnew.wxPoint(*newposition))

                pivot_mod_flipped = mod_to_clone.mod.IsFlipped()
                if (mod.mod.IsFlipped() and not pivot_mod_flipped) or (pivot_mod_flipped and not mod.mod.IsFlipped()):
                    flip_module(mod.mod, mod.mod.GetPosition())
                    # mod.mod.Flip(mod.mod.GetPosition())

                mod.mod.SetOrientationDegrees(new_orientation)

                # Copy local settings.
                mod.mod.SetLocalClearance(mod_to_clone.mod.GetLocalClearance())
                mod.mod.SetLocalSolderMaskMargin(mod_to_clone.mod.GetLocalSolderMaskMargin())
                mod.mod.SetLocalSolderPasteMargin(mod_to_clone.mod.GetLocalSolderPasteMargin())
                mod.mod.SetLocalSolderPasteMarginRatio(mod_to_clone.mod.GetLocalSolderPasteMarginRatio())
                mod.mod.SetZoneConnection(mod_to_clone.mod.GetZoneConnection())

            # replicate also text layout - also for anchor module. I am counting that the user is lazy and will
            # just position the anchors and will not edit them
            # get pivot_module_text
            # get module text
            pivot_mod_text_items = get_module_text_items(mod_to_clone)
            mod_text_items = get_module_text_items(mod)
            # replicate each text item
            for pivot_text in pivot_mod_text_items:
                index = pivot_mod_text_items.index(pivot_text)
                pivot_text_position = pivot_text.GetPosition() + anchor_delta_pos

                newposition = rotate_around_pivot_point(pivot_text_position, anchor_pos, anchor_delta_angle)

                # convert to tuple of integers
                newposition = [int(x) for x in newposition]
                mod_text_items[index].SetPosition(pcbnew.wxPoint(*newposition))

                # set orientation
                mod_text_items[index].SetTextAngle(pivot_text.GetTextAngle())
                # thickness
                mod_text_items[index].SetThickness(pivot_text.GetThickness())
                # width
                mod_text_items[index].SetTextWidth(pivot_text.GetTextWidth())
                # height
                mod_text_items[index].SetTextHeight(pivot_text.GetTextHeight())
                # rest of the parameters
                # TODO check SetEffects method, might be better
                mod_text_items[index].SetItalic(pivot_text.IsItalic())
                mod_text_items[index].SetBold(pivot_text.IsBold())
                mod_text_items[index].SetMirrored(pivot_text.IsMirrored())
                mod_text_items[index].SetMultilineAllowed(pivot_text.IsMultilineAllowed())
                mod_text_items[index].SetHorizJustify(pivot_text.GetHorizJustify())
                mod_text_items[index].SetVertJustify(pivot_text.GetVertJustify())
                # set visibility
                mod_text_items[index].SetVisible(pivot_text.IsVisible())

    def replicate_tracks(self, pivot_anchor_mod, pivot_tracks, anchor_mod, net_pairs):
        logger.info("Replicating tracks")

        # get anchor module
        mod2 = anchor_mod
        # get anchor angle with respect to pivot module
        mod2_angle = mod2.mod.GetOrientation()
        # get exact anchor position
        mod2_pos = mod2.mod.GetPosition()

        mod1_angle = pivot_anchor_mod.mod.GetOrientation()
        mod1_pos = pivot_anchor_mod.mod.GetPosition()

        move_vector = mod2_pos - mod1_pos
        delta_orientation = mod2_angle - mod1_angle

        net_pairs, net_dict = net_pairs

        # go through all the tracks
        for track in pivot_tracks:
            # get from which net we are clonning
            from_net_name = track.GetNetname()
            # find to net
            tup = [item for item in net_pairs if item[0] == from_net_name]
            # if net was not fount, then the track is not part of this sheet and should not be cloned
            if not tup:
                pass
            else:
                to_net_name = tup[0][1]
                to_net_code = net_dict[to_net_name].GetNet()
                to_net_item = net_dict[to_net_name]

                # make a duplicate, move it, rotate it, select proper net and add it to the board
                new_track = track.Duplicate()
                self.board.Add(new_track)
                new_track.Rotate(mod1_pos, delta_orientation)
                new_track.Move(move_vector)
                logger.info("Setting track net to: " + repr(to_net_code) + ", " + repr(to_net_name))
                new_track.SetNetCode(to_net_code)
                new_track.SetNet(to_net_item)  # assert crash if board.Add after this line

    def replicate_zones(self, pivot_anchor_mod, pivot_zones, anchor_mod, net_pairs):
        """ method which replicates zones"""
        logger.info("Replicating zones")

        # get anchor module
        mod2 = anchor_mod
        # get anchor angle with respect to pivot module
        mod2_angle = mod2.mod.GetOrientation()
        # get exact anchor position
        mod2_pos = mod2.mod.GetPosition()

        mod1_angle = pivot_anchor_mod.mod.GetOrientation()
        mod1_pos = pivot_anchor_mod.mod.GetPosition()

        move_vector = mod2_pos - mod1_pos
        delta_orientation = mod2_angle - mod1_angle

        net_pairs, net_dict = net_pairs
        # go through all the zones
        for zone in pivot_zones:
            # get from which net we are clonning
            from_net_name = zone.GetNetname()
            # if zone is not on copper layer it does not matter on which net it is
            if not zone.IsOnCopperLayer():
                tup = [(u'', u'')]
            else:
                tup = [item for item in net_pairs if item[0] == from_net_name]

            # there is no net
            if not tup:
                # Allow keepout zones to be cloned.
                if zone.GetIsKeepout():
                    tup = [(u'', u'')]
                # do not clone
                else:
                    logger.info('Skipping replication of a zone')
                    continue

            # start the clone
            to_net_name = tup[0][1]
            if to_net_name == u'':
                to_net_item = self.board.FindNet(to_net_name)
                to_net_code = to_net_item.GetNet()
            else:
                to_net_code = net_dict[to_net_name].GetNet()
                to_net_item = net_dict[to_net_name]

            # make a duplicate, move it, rotate it, select proper net and add it to the board
            new_zone = zone.Duplicate()
            self.board.Add(new_zone)
            new_zone.Rotate(mod1_pos, delta_orientation)
            new_zone.Move(move_vector)
            new_zone.SetNetCode(to_net_code)
            new_zone.SetNet(to_net_item) # assert crash if board.Add after this line

    def replicate_text(self, pivot_anchor_mod, pivot_text, anchor_mod):
        logger.info("Replicating text")

        # get anchor angle with respect to pivot module
        anchor_angle = anchor_mod.mod.GetOrientationDegrees()
        # get exact anchor position
        anchor_pos = anchor_mod.mod.GetPosition()

        anchor_delta_angle = pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
        anchor_delta_pos = anchor_pos - pivot_anchor_mod.mod.GetPosition()

        for text in pivot_text:
            new_text = text.Duplicate()
            new_text.Move(anchor_delta_pos)
            new_text.Rotate(anchor_pos, -anchor_delta_angle * 10)
            self.board.Add(new_text)

    def replicate_drawings(self, pivot_anchor_mod, pivot_drawings, anchor_mod):
        logger.info("Replicating drawings")
        # get anchor angle with respect to pivot module
        anchor_angle = anchor_mod.mod.GetOrientationDegrees()
        # get exact anchor position
        anchor_pos = anchor_mod.mod.GetPosition()

        anchor_delta_angle = pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
        anchor_delta_pos = anchor_pos - pivot_anchor_mod.mod.GetPosition()

        # go through all the drawings
        for drawing in pivot_drawings:

            new_drawing = drawing.Duplicate()
            new_drawing.Move(anchor_delta_pos)
            new_drawing.Rotate(anchor_pos, -anchor_delta_angle * 10)

            self.board.Add(new_drawing)

    def restore_layout(self, anchor_mod, layout_file):
        logger.info("Loading saved design")
        # load saved design
        with open(layout_file, 'rb') as f:
            data_saved = pickle.load(f)

        # get saved hierarchy
        source_level_filename = data_saved.level_filename
        logger.info("Source level is:" + repr(source_level_filename))

        # find the corresponding hierarchy in the target layout
        # this is tricky as target design might be shallower or deeper than source design

        # so one takes the last source level only
        last_level = source_level_filename[-1]
        logger.info("Destination footprint is:" + repr(anchor_mod.ref))
        logger.info("Destination levels available are:" + repr(anchor_mod.filename))

        # check if saved (source) hierarchy is available in destination
        if not all(item in anchor_mod.filename for item in source_level_filename):
            raise LookupError(  "Destination hierarchy: " + repr(anchor_mod.filename) + "\n"
                              + "does not match source hierarchy: " + repr(source_level_filename))

        indx = anchor_mod.filename.index(last_level)
        level = anchor_mod.sheetname[0:indx+1]

        destination_level_filename = anchor_mod.filename[0:indx+1]
        logger.info("Destination level is:" + repr(destination_level_filename))

        # load schematics and calculate hash of schematics (you have to support nested hierarchy)
        list_of_sheet_files = anchor_mod.filename[len(destination_level_filename)-1:]

        logger.info("All sch files required are: " + repr(list_of_sheet_files))

        logger.info("Getting current schematics hash")
        md5hash = hashlib.md5()
        for sch_file in list_of_sheet_files:
            md5hash = self.schematics.get_sch_hash(sch_file, md5hash)

        hex_hash = md5hash.hexdigest()

        # check the hash
        saved_hash = data_saved.hash

        logger.info("Source hash is:" + repr(saved_hash))
        logger.info("Destination hash is: " + repr(hex_hash))

        if not saved_hash == hex_hash:
            raise ValueError("Source and destination schematics don't match!")

        # save board from the saved layout only temporary
        tempdir = tempfile.gettempdir()
        temp_filename = os.path.join(tempdir, 'temp_layout_for_restore.kicad_pcb')
        with open(temp_filename, 'wb') as f:
            f.write(data_saved.layout.encode('utf-8'))

        # restore layout data
        saved_board = pcbnew.LoadBoard(temp_filename)
        # delete temporary file
        os.remove(temp_filename)

        # get layout data from saved board
        logger.info("Get layout data from saved board")
        saved_layout = PcbData(saved_board)
        saved_layout.set_modules_hierarchy_names(data_saved.dict_of_sheets)

        modules_saved = saved_layout.modules

        modules_to_place = self.layout.get_modules_on_sheet(level)

        # check if saved layout and layotu to be restored match at least in footprint count
        if len(modules_to_place) != len(modules_saved):
            raise ValueError("Source and destination footprint count don't match!")

        # sort by ID - I am counting that source and destination sheed have been
        # anotated by KiCad in their final form (reset anotation and then re-anotate)
        modules_to_place = sorted(modules_to_place, key=lambda x: (x.mod_id, x.ref))
        modules_saved = sorted(modules_saved, key=lambda x: (x.mod_id, x.ref))

        # get the saved layout ID numbers and try to figure out a match (at least the same depth, ...)
        # find net pairs
        net_pairs = self.get_net_pairs(modules_to_place, modules_saved)

        # replicate modules
        pivot_anchor_mod = modules_saved[modules_to_place.index(anchor_mod)]
        self.replicate_modules(pivot_anchor_mod, modules_saved, anchor_mod, modules_to_place)

        # replicate tracks
        self.replicate_tracks(pivot_anchor_mod, saved_board.GetTracks(), anchor_mod, net_pairs)

        # replicate zones
        pivot_zones = [saved_board.GetArea(zone_id) for zone_id in range(saved_board.GetAreaCount()) ]
        self.replicate_zones(pivot_anchor_mod, pivot_zones, anchor_mod, net_pairs)

        # replicate text
        pivot_text = [item for item in saved_board.GetDrawings() if isinstance(item, pcbnew.TEXTE_PCB)]
        self.replicate_text(pivot_anchor_mod, pivot_text, anchor_mod)

        # replicate drawings
        pivot_drawings = [item for item in saved_board.GetDrawings() if isinstance(item, pcbnew.DRAWSEGMENT)]
        self.replicate_drawings(pivot_anchor_mod, pivot_drawings, anchor_mod)
        pass


class SaveLayout(RestoreLayout):
    # overwrites the master class init
    def __init__(self, board):
        logger.info("Saving the current board temporary in order to leave current layout intact")
        # generate new tempfile
        tempdir = tempfile.gettempdir()
        self.tempfilename = os.path.join(tempdir, 'temp_boardfile_for_save.kicad_pcb')
        if os.path.isfile(self.tempfilename):
            os.remove(self.tempfilename)
        pcbnew.SaveBoard(self.tempfilename, board)
        self.board = pcbnew.LoadBoard(self.tempfilename)

        # create a copy of the board and then work on the copy
        logger.info("Getting schematics info")
        self.schematics = SchData(board)
        logger.info("Getting layout info")
        self.layout = PcbData(self.board)
        logger.info("Updating layout info with schematics info")
        self.layout.set_modules_hierarchy_names(self.schematics.dict_of_sheets)

    def remove_drawings(self, bounding_box, containing):
        logger.info("Removing drawing")
        # remove all drawings outside of bounding box
        drawings_to_delete = []
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.DRAWSEGMENT):
                continue
            drawing_bb = drawing.GetBoundingBox()
            if containing:
                if not bounding_box.Contains(drawing_bb):
                    drawings_to_delete.append(drawing)
            else:
                if bounding_box.Intersects(drawing_bb):
                    drawings_to_delete.append(drawing)
        for dwg in drawings_to_delete:
            self.board.RemoveNative(dwg)

    def remove_text(self, bounding_box, containing):
        logger.info("Removing text")
        # remove all text outside of bounding box
        text_to_delete = []
        for text in self.board.GetDrawings():
            if not isinstance(text, pcbnew.TEXTE_PCB):
                continue
            text_bb = text.GetBoundingBox()
            if containing:
                if not bounding_box.Contains(text_bb):
                    text_to_delete.append(text)
            else:
                if bounding_box.Intersects(text_bb):
                    text_to_delete.append(text)
        for txt in text_to_delete:
            self.board.RemoveNative(txt)

    def remove_zones(self, bounding_box, containing):
        logger.info("Removing zones")
        # remove all zones outisde of bounding box
        all_zones = []
        for zoneid in range(self.board.GetAreaCount()):
            all_zones.append(self.board.GetArea(zoneid))
        # find all zones which are outside the pivot bounding box
        for zone in all_zones:
            zone_bb = zone.GetBoundingBox()
            if containing:
                if not bounding_box.Contains(zone_bb):
                    self.board.RemoveNative(zone)
            else:
                if not bounding_box.Intersects(zone_bb):
                    self.board.RemoveNative(zone)

    def remove_tracks(self, bounding_box, containing):
        logger.info("Removing tracks")

        logger.info("Bounding box points: "
                    + repr((bounding_box.GetTop(), bounding_box.GetBottom(), bounding_box.GetLeft(), bounding_box.GetRight())))
        # find all tracks within the pivot bounding box
        # construct a python list as in 5.99 deque hase issues if we delete an item
        # TODO might be smarter to iterate thorugh original deque and instead of deleting tracks immediately,
        # TODO add them to new list and only then delete them
        tracks_to_delete = []
        # get all the tracks for replication
        for track in self.board.GetTracks():
            track_bb = track.GetBoundingBox()
            # if track is contained or intersecting the bounding box
            if containing:
                if not bounding_box.Contains(track_bb):
                    tracks_to_delete.append(track)
            else:
                if not bounding_box.Intersects(track_bb):
                    tracks_to_delete.append(track)
        for trk in tracks_to_delete:
            self.board.RemoveNative(trk)

    def remove_modules(self, modules):
        logger.info("Removing modules")
        for mod in modules:
            self.board.RemoveNative(mod.mod)

    def save_layout(self, src_anchor_mod, level, data_file):
        logger.info("Saving layout for level: " + repr(level))
        logger.info("Calculating hash of the layout schematics")
        # load schematics and calculate hash of schematics (you have to support nested hierarchy)
        list_of_sheet_files = src_anchor_mod.filename[len(level) - 1:]

        logger.info("Saving hash for files: " + repr(list_of_sheet_files))

        md5hash = hashlib.md5()
        for sch_file in list_of_sheet_files:
            md5hash = self.schematics.get_sch_hash(sch_file, md5hash)

        hex_hash = md5hash.hexdigest()

        # get modules on a sheet
        src_modules = self.layout.get_modules_on_sheet(level)
        logging.info("Source modules are: " + repr([x.ref for x in src_modules]))

        # get other modules
        other_modules = self.layout.get_modules_not_on_sheet(level)
        # get nets local to pivot modules
        local_nets = self.layout.get_local_nets(src_modules, other_modules)

        # get modules bounding box
        bounding_box = self.layout.get_modules_bounding_box(src_modules)

        logger.info("Removing everything else from the layout")

        # remove text items
        self.remove_text(bounding_box, True)

        # remove drawings
        self.remove_drawings(bounding_box, True)

        # remove zones
        self.remove_zones(bounding_box, True)

        # remove tracks
        self.remove_tracks(bounding_box, True)

        # remove modules
        other_modules = self.layout.get_modules_not_on_sheet(level)
        self.remove_modules(other_modules)

        # save the layout
        logger.info("Saving layout in temporary file")
        pcbnew.SaveBoard(self.tempfilename, self.board)
        # load as text
        logger.info("Reading layout as text")
        with open(self.tempfilename, 'rb') as f:
            layout = f.read().decode('utf-8')

        # remove the file
        os.remove(self.tempfilename)

        logger.info("Saving layout data")
        # level_filename, level
        level_filename = [src_anchor_mod.filename[src_anchor_mod.sheetname.index(x)] for x in level]
        # save all data
        data_to_save = LayoutData(layout, hex_hash, self.schematics.dict_of_sheets, local_nets, level, level_filename)
        with open(data_file, 'wb') as f:
            pickle.dump(data_to_save, f, 0)
        logger.info("Succesfully saved the layout")


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Source_project"))
    source_file = 'multiple_hierarchy.kicad_pcb'

    board = pcbnew.LoadBoard(source_file)
    save_layout = SaveLayout(board)

    pivot_mod_ref = 'Q301'
    pivot_mod = save_layout.get_mod_by_ref(pivot_mod_ref)

    levels = pivot_mod.filename
    # get the level index from user
    index = levels.index(levels[1])

    data_file = 'source_layout_test.pckl'
    save_layout.save_layout(pivot_mod, pivot_mod.sheetname[0:index + 1], data_file)

    logger.info("--- layout saved succesfully --")
    logger.info("--- proceeding with restoring --")

    # restore layout
    data_file = os.path.abspath(data_file)
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Destination_project"))
    destination_file = 'Destination_project.kicad_pcb'
    board = pcbnew.LoadBoard(destination_file)
    restore_layout = RestoreLayout(board)

    pivot_mod_ref = 'Q3'
    pivot_mod = restore_layout.get_mod_by_ref(pivot_mod_ref)

    restore_layout.restore_layout(pivot_mod, data_file)

    saved = pcbnew.SaveBoard(destination_file.replace(".kicad_pcb", "_temp.kicad_pcb"), board)

    b = 2
    

# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    logging.basicConfig(level=logging.DEBUG,
                        filename="save_restore_layout.log",
                        filemode='w',
                        format='%(lineno)d:%(message)s',
                        datefmt=None)

    logger = logging.getLogger(__name__)
    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("Save/Restore Layout plugin started in standalone mode")

    main()
