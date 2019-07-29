# -*- coding: utf-8 -*-
#  replicate_layout_V2.py
#
# Copyright (C) 2019 Mitja Nemec, Stephen Walker-Weinshenker, Hildo Guillardi Júnior
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

parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
if __name__ == '__main__' or parent_module.__name__ == '__main__':
    import compare_boards
else:
    from . import compare_boards

Module = namedtuple('Module', ['ref', 'mod', 'mod_id', 'sheet_id', 'filename'])
logger = logging.getLogger(__name__)

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()


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


def get_index_of_tuple(list_of_tuples, index, value):
    for pos, t in enumerate(list_of_tuples):
        if t[index] == value:
            return pos


def get_module_text_items(module):
    """ get all text item belonging to a modules """
    list_of_items = [module.mod.Reference(), module.mod.Value()]

    module_items = module.mod.GraphicalItemsList()
    for item in module_items:
        if type(item) is pcbnew.TEXTE_MODULE:
            list_of_items.append(item)
    return list_of_items


# this function was made by Miles Mccoo
# https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
def get_coordinate_points_of_shape_poly_set(ps):
    string = ps.Format()
    lines = string.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]]  # -1 because of the extra two \n
    return pts


class Replicator():
    @staticmethod
    def extract_subsheets(filename):
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
                # found sheet name
                if line.startswith('F0 '):
                    # remove the first field ("F0 ")
                    partial_line = line.lstrip("F0 ")
                    partial_line = " ".join(partial_line.split()[:-1])
                    # remove the last field (text size)
                    subsheet_name = partial_line.rstrip("\"").lstrip("\"")
                # found sheet filename
                if line.startswith('F1 '):
                    subsheet_path = re.findall("\s\"(.*.sch)\"\s", line)[0]
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
            yield file_path, subsheet_id, subsheet_name

    def find_all_sch_files(self, filename, dict_of_sheets):
        for file_path, subsheet_id, subsheet_name in self.extract_subsheets(filename):
            dict_of_sheets[subsheet_id] = [subsheet_name, file_path]
            dict_of_sheets = self.find_all_sch_files(file_path, dict_of_sheets)
        return dict_of_sheets

    @staticmethod
    def get_module_id(module):
        """ get module id """
        module_path = module.GetPath().split('/')
        module_id = "/".join(module_path[-1:])
        return module_id

    def get_sheet_id(self, module):
        """ get sheet id """
        module_path = module.GetPath().split('/')
        sheet_id = module_path[0:-1]
        sheet_names = [self.dict_of_sheets[x][0] for x in sheet_id if x]
        sheet_files = [self.dict_of_sheets[x][1] for x in sheet_id if x]
        sheet_id = [sheet_names, sheet_files]
        return sheet_id

    def get_mod_by_ref(self, ref):
        for m in self.modules:
            if m.ref == ref:
                return m
        return None

    def __init__(self, board):
        self.board = board
        self.pcb_filename = os.path.abspath(board.GetFileName())
        self.sch_filename = self.pcb_filename.replace(".kicad_pcb", ".sch")
        self.project_folder = os.path.dirname(self.pcb_filename)

        # test if sch file exist
        if not os.path.isfile(self.sch_filename):
            raise LookupError("Schematics file " + self.sch_filename + " does not exist!")

        # get relation between sheetname and it's id
        logger.info('getting project hierarchy from schematics')
        self.dict_of_sheets = self.find_all_sch_files(self.sch_filename, {})
        logger.info("Project hierarchy looks like:\n%s" % repr(self.dict_of_sheets))

        # make all paths relative
        for x in self.dict_of_sheets.keys():
            path = self.dict_of_sheets[x][1]
            self.dict_of_sheets[x] = [self.dict_of_sheets[x][0], os.path.relpath(path, self.project_folder)]

        # construct a list of modules with all pertinent data 
        logger.info('getting a list of all footprints on board') 
        bmod = board.GetModules()
        self.modules = []
        mod_dict = {}
        for module in bmod:
            mod_named_tuple = Module(mod=module,
                                     mod_id=self.get_module_id(module),
                                     sheet_id=self.get_sheet_id(module)[0],
                                     filename=self.get_sheet_id(module)[1], 
                                     ref=module.GetReference())
            mod_dict[module.GetReference()] = mod_named_tuple
            self.modules.append(mod_named_tuple)
        pass

    def get_list_of_modules_with_same_id(self, id):
        list_of_modules = []
        for m in self.modules:
            if m.mod_id == id:
                list_of_modules.append(m)
        return list_of_modules

    def get_sheets_to_replicate(self, mod, level):
        # TODO - tukaj nekje tici hrosc
        sheet_id = mod.sheet_id
        sheet_file = mod.filename
        # poisci level_id
        level_file = sheet_file[sheet_id.index(level)]
        logger.info('construcing a list of sheets suitable for replication on level:'+repr(level)+", file:"+repr(level_file))

        sheet_id_up_to_level = []
        for i in range(len(sheet_id)):
            sheet_id_up_to_level.append(sheet_id[i])
            if sheet_id[i] == level:
                break
        logger.debug("Sheet ids up to the level:" + repr(sheet_id_up_to_level))

        # get all footprints with same ID
        list_of_modules = self.get_list_of_modules_with_same_id(mod.mod_id)
        logger.debug("Footprints on the sheets:\n" + repr([x.ref for x in list_of_modules]))

        # log all modules sheet id
        logger.debug("Footprints raw sheet ids:\n" + repr([x.mod.GetPath() for x in list_of_modules]))

        # if hierarchy is deeper, match only the sheets with same hierarchy from root to -1
        all_sheets = []

        # pojdi cez vse footprinte z istim ID-jem
        for m in list_of_modules:
            # in ce ta footprint je na tem nivoju, dodaj ta sheet v seznam
            if level_file in m.filename:
                sheet_id_list = []
                # sestavi hierarhično pot samo do nivoja do katerega želimo
                for i in range(len(m.filename)):
                    sheet_id_list.append(m.sheet_id[i])
                    if m.filename[i] == level_file:
                        break
                all_sheets.append(sheet_id_list)
        logger.debug("All sheets to replicate:\n" + repr(all_sheets))

        # remove duplicates
        all_sheets.sort()
        all_sheets = list(k for k, _ in itertools.groupby(all_sheets))
        logger.debug("All sheets to replicate sorted:\n" + repr(all_sheets))

        # remove pivot_sheet
        if sheet_id_up_to_level in all_sheets:
            index = all_sheets.index(sheet_id_up_to_level)
            del all_sheets[index]
        logger.info("All sheets to replicate sorted and without pivot_sheet:\n" + repr(all_sheets))

        return all_sheets

    def get_modules_on_sheet(self, level):
        modules_on_sheet = []
        level_depth = len(level)
        for mod in self.modules:
            if level == mod.sheet_id[0:level_depth]:
                modules_on_sheet.append(mod)
        return modules_on_sheet

    def get_modules_not_on_sheet(self, level):
        modules_not_on_sheet = []
        level_depth = len(level)
        for mod in self.modules:
            if level != mod.sheet_id[0:level_depth]:
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

    def get_modules_bounding_box(self, modules):
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

    def get_sheet_anchor_module(self, sheet):
        # get all modules on this sheet
        mod_sheet = self.get_modules_on_sheet(sheet)
        # get anchor module
        list_of_possible_anchor_modules = []
        for mod in mod_sheet:
            if mod.mod_id == self.pivot_anchor_mod.mod_id:
                list_of_possible_anchor_modules.append(mod)

        # if there is more than one possible anchor, select the correct one
        if len(list_of_possible_anchor_modules) == 1:
            anchor_mod = list_of_possible_anchor_modules[0]
        else:
            list_of_mathces = []
            for mod in list_of_possible_anchor_modules:
                index = list_of_possible_anchor_modules.index(mod)
                matches = 0
                for item in self.pivot_anchor_mod.sheet_id:
                    if item in mod.sheet_id:
                        matches = matches + 1
                list_of_mathces.append((index, matches))
            # todo select the one with most matches
            index, _ = max(list_of_mathces, key=lambda item: item[1])
            anchor_mod = list_of_possible_anchor_modules[index]
        return anchor_mod

    def get_net_pairs(self, sheet):
        """ find all net pairs between pivot sheet and current sheet"""
        # find all modules, pads and nets on this sheet
        sheet_modules = self.get_modules_on_sheet(sheet)

        # find all net pairs via same modules pads,
        net_pairs = []
        net_dict = {}
        # construct module pairs
        mod_matches = []
        for p_mod in self.pivot_modules:
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
                index = get_index_of_tuple(p_nets, 1, net[1])
                net_pairs.append((p_nets[index][1], s_nets[index][1]))

        # remove duplicates
        net_pairs_clean = list(set(net_pairs))

        return net_pairs_clean, net_dict

    def prepare_for_replication(self, level, containing):
        # get a list of modules for replication
        logger.info("Getting the list of pivot footprints")
        self.pivot_modules = self.get_modules_on_sheet(level)
        # get the rest of the modules
        logger.info("Getting the list of all the remaining footprints")
        self.other_modules = self.get_modules_not_on_sheet(level)
        # get nets local to pivot modules
        logger.info("Getting nets local to pivot footprints")
        self.pivot_local_nets = self.get_local_nets(self.pivot_modules, self.other_modules)
        # get pivot bounding box
        logger.info("Getting pivot bounding box")
        self.pivot_bounding_box = self.get_modules_bounding_box(self.pivot_modules)
        # get pivot tracks
        logger.info("Getting pivot tracks")
        self.pivot_tracks = self.get_tracks(self.pivot_bounding_box, self.pivot_local_nets, containing)
        # get pivot zones
        logger.info("Getting pivot zones")
        self.pivot_zones = self.get_zones(self.pivot_bounding_box, containing)
        # get pivot text items
        logger.info("Getting pivot text items")
        self.pivot_text = self.get_text_items(self.pivot_bounding_box, containing)
        # get pivot drawings
        logger.info("Getting pivot text items")
        self.pivot_drawings = self.get_drawings(self.pivot_bounding_box, containing)

    def replicate_modules(self):
        logger.info("Replicating footprints")
        for sheet in self.sheets_for_replication:
            logger.info("Replicating footprints on sheet " + repr(sheet))
            # get anchor module
            anchor_mod = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to pivot module
            anchor_angle = anchor_mod.mod.GetOrientationDegrees()
            # get exact anchor position
            anchor_pos = anchor_mod.mod.GetPosition()

            anchor_delta_angle = self.pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
            anchor_delta_pos = anchor_pos - self.pivot_anchor_mod.mod.GetPosition()

            # go through all modules
            mod_sheet = self.get_modules_on_sheet(sheet)
            for mod in mod_sheet:
                # find proper match in pivot modules
                mod_to_clone = None
                list_of_possible_pivot_modules = []
                for pmod in self.pivot_modules:
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
                pivot_anchor_pos = self.pivot_anchor_mod.mod.GetPosition()
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
                        mod.mod.Flip(mod.mod.GetPosition())
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
                # check if both modules (pivot and the one for replication) have the same number of text items
                if len(pivot_mod_text_items) != len(mod_text_items):
                    raise LookupError("Pivot module: " + mod_to_clone.ref + " has different number of text items (" + repr(len(pivot_mod_text_items)) 
                                      + ")\nthan module for replication: " + mod.ref + " (" + repr(len(mod_text_items)) + ")")
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

    def replicate_tracks(self):
        logger.info("Replicating tracks")
        for sheet in self.sheets_for_replication:
            logger.info("Replicating tracks on sheet " + repr(sheet))
            # get anchor module
            anchor_mod = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to pivot module
            anchor_angle = anchor_mod.mod.GetOrientationDegrees()
            # get exact anchor position
            anchor_pos = anchor_mod.mod.GetPosition()

            anchor_delta_angle = self.pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
            anchor_delta_pos = anchor_pos - self.pivot_anchor_mod.mod.GetPosition()

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
                    # this came partially from Miles Mccoo
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

                        # get module to clone position
                        pivot_track_pos = track.GetPosition()
                        # get relative position with respect to pivot anchor
                        pivot_anchor_pos = self.pivot_anchor_mod.mod.GetPosition()
                        pivot_mod_delta_pos = pivot_track_pos - pivot_anchor_pos

                        # new orientation is simple
                        old_position = pivot_mod_delta_pos + anchor_pos
                        newposition = rotate_around_pivot_point(old_position, anchor_pos, anchor_delta_angle)

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

                        # get module to clone position
                        pivot_track_pos = track.GetStart()
                        # get relative position with respect to pivot anchor
                        pivot_anchor_pos = self.pivot_anchor_mod.mod.GetPosition()
                        pivot_mod_delta_pos = pivot_track_pos - pivot_anchor_pos

                        # new orientation is simple
                        old_position = pivot_mod_delta_pos + anchor_pos
                        newposition = rotate_around_pivot_point(old_position, anchor_pos, anchor_delta_angle)
                        newposition = [int(x) for x in newposition]
                        newtrack.SetStart(pcbnew.wxPoint(*newposition))

                        pivot_track_pos = track.GetEnd()
                        # get relative position with respect to pivot anchor
                        pivot_anchor_pos = self.pivot_anchor_mod.mod.GetPosition()
                        pivot_mod_delta_pos = pivot_track_pos - pivot_anchor_pos

                        # new orientation is simple
                        old_position = pivot_mod_delta_pos + anchor_pos
                        newposition = rotate_around_pivot_point(old_position, anchor_pos, anchor_delta_angle)
                        newposition = [int(x) for x in newposition]
                        newtrack.SetEnd(pcbnew.wxPoint(*newposition))

                        newtrack.SetWidth(track.GetWidth())
                        newtrack.SetLayer(track.GetLayer())

                        newtrack.SetNet(to_net)

    def replicate_zones(self):
        """ method which replicates zones"""
        logger.info("Replicating zones")
        # start cloning
        for sheet in self.sheets_for_replication:
            logger.info("Replicating zones on sheet " + repr(sheet))

            # get anchor module
            mod2 = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to pivot module
            mod2_angle = mod2.mod.GetOrientation()
            # get exact anchor position
            mod2_pos = mod2.mod.GetPosition()

            mod1_angle = self.pivot_anchor_mod.mod.GetOrientation()
            mod1_pos = self.pivot_anchor_mod.mod.GetPosition()

            move_vector = mod2_pos - mod1_pos
            delta_orientation = mod2_angle - mod1_angle

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
                        logger.info('Skipping replication of a zone on copper layer without a net')
                        continue

                # start the clone
                to_net_name = tup[0][1]
                if to_net_name == u'':
                    to_net = 0
                else:
                    to_net = net_dict[to_net_name].GetNet()

                # make a duplicate, move it, rotate it, select proper net and add it to the board
                new_zone = zone.Duplicate()
                new_zone.Rotate(mod1_pos, delta_orientation)
                new_zone.Move(move_vector)
                new_zone.SetNetCode(to_net)
                self.board.Add(new_zone)

    def replicate_text(self):
        logger.info("Replicating text")
        # start cloning
        for sheet in self.sheets_for_replication:
            logger.info("Replicating text on sheet " + repr(sheet))
            # get anchor module
            anchor_mod = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to pivot module
            anchor_angle = anchor_mod.mod.GetOrientationDegrees()
            # get exact anchor position
            anchor_pos = anchor_mod.mod.GetPosition()

            anchor_delta_angle = self.pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
            anchor_delta_pos = anchor_pos - self.pivot_anchor_mod.mod.GetPosition()

            for text in self.pivot_text:
                new_text = text.Duplicate()
                new_text.Move(anchor_delta_pos)
                new_text.Rotate(anchor_pos, -anchor_delta_angle * 10)
                self.board.Add(new_text)

    def replicate_drawings(self):
        logger.info("Replicating drawings")
        for sheet in self.sheets_for_replication:
            logger.info("Replicating drawings on sheet " + repr(sheet))
            # get anchor module
            anchor_mod = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to pivot module
            anchor_angle = anchor_mod.mod.GetOrientationDegrees()
            # get exact anchor position
            anchor_pos = anchor_mod.mod.GetPosition()

            anchor_delta_angle = self.pivot_anchor_mod.mod.GetOrientationDegrees() - anchor_angle
            anchor_delta_pos = anchor_pos - self.pivot_anchor_mod.mod.GetPosition()

            # go through all the drawings
            for drawing in self.pivot_drawings:

                new_drawing = drawing.Duplicate()
                new_drawing.Move(anchor_delta_pos)
                new_drawing.Rotate(anchor_pos, -anchor_delta_angle * 10)
                
                self.board.Add(new_drawing)


    def remove_zones_tracks(self, containing):
        for sheet in self.sheets_for_replication:
            # get modules on a sheet
            mod_sheet = self.get_modules_on_sheet(sheet)
            # get bounding box
            bounding_box = self.get_modules_bounding_box(mod_sheet)

            # from all the tracks on board
            all_tracks = self.board.GetTracks()
            # remove the tracks that are not on nets contained in this sheet
            nets_on_sheet = self.get_nets_from_modules(mod_sheet)
            tracks_on_nets_on_sheet = []
            for track in all_tracks:
                if track.GetNetname() in nets_on_sheet:
                    tracks_on_nets_on_sheet.append(track)

            for track in tracks_on_nets_on_sheet:
                # minus the tracks in pivot bounding box
                if track not in self.pivot_tracks:
                    track_bounding_box = track.GetBoundingBox()
                    # remove the tracks containing/interesecting in the replicated bounding box
                    if containing:
                        if bounding_box.Contains(track_bounding_box):
                            self.board.RemoveNative(track)
                    else:
                        if bounding_box.Intersects(track_bounding_box):
                            self.board.RemoveNative(track)

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
                    zone_bounding_box = zone.GetBoundingBox()
                    # remove the zones containing/interesecting in the replicated bounding box
                    if containing:
                        if bounding_box.Contains(zone_bounding_box):
                            self.board.RemoveNative(zone)
                    else:
                        if bounding_box.Intersects(zone_bounding_box):
                            self.board.RemoveNative(zone)

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
                if containing:
                    if bounding_box.Contains(text_bb):
                        self.board.RemoveNative(drawing)
                else:
                    if bounding_box.Intersects(text_bb):
                        self.board.RemoveNative(drawing)

            # from all drawing items on the board
            for drawing in self.board.GetDrawings():
                if not isinstance(drawing, pcbnew.DRAWSEGMENT):
                    continue
                # ignore text in the pivot sheet
                if drawing in self.pivot_drawings:
                    continue

                # add text in/intersecting with the replicated bounding box to
                # the list for removal.
                dwg_bb = drawing.GetBoundingBox()
                if containing:
                    if bounding_box.Contains(dwg_bb):
                        self.board.RemoveNative(drawing)
                else:
                    if bounding_box.Intersects(dwg_bb):
                        self.board.RemoveNative(drawing)

    def replicate_layout(self, pivot_mod, level, sheets_for_replication,
                         containing, remove, tracks, zones, text, drawings):
        logger.info( "Starting replication of sheets: " + repr(sheets_for_replication)
                    +"\non level: " + repr(level)
                    +"\nwith tracks="+repr(tracks)+", zone="+repr(zones)+", text="+repr(text)
                    +", containing="+repr(containing)+", remov="+repr(remove))
        self.level = level
        self.pivot_anchor_mod = pivot_mod
        self.sheets_for_replication = sheets_for_replication

        # get pivot(anchor) module details
        self.pivot_mod_orientation = self.pivot_anchor_mod.mod.GetOrientationDegrees()
        self.pivot_mod_position = self.pivot_anchor_mod.mod.GetPosition()
        self.prepare_for_replication(level, containing)
        if remove:
            logger.info("Removing tracks and zones, before module placement")
            self.remove_zones_tracks(containing)
        self.replicate_modules()
        if remove:
            logger.info("Removing tracks and zones, after module placement")
            self.remove_zones_tracks(containing)
        if tracks:
            self.replicate_tracks()
        if zones:
            self.replicate_zones()
        if text:
            self.replicate_text()
        if drawings:
            self.replicate_drawings()

def test_file(in_filename, out_filename, pivot_mod_ref, level, sheets, containing, remove):
    board = pcbnew.LoadBoard(in_filename)
    # get board information
    replicator = Replicator(board)
    # get pivot module info
    pivot_mod = replicator.get_mod_by_ref(pivot_mod_ref)
    # have the user select replication level
    levels = pivot_mod.filename
    # get the level index from user
    index = levels.index(levels[level])
    # get list of sheets
    sheet_list = replicator.get_sheets_to_replicate(pivot_mod, pivot_mod.sheet_id[index])
    
    # get acnhor modules
    anchor_modules = replicator.get_list_of_modules_with_same_id(pivot_mod.mod_id)
    # find matching anchors to maching sheets
    ref_list = []
    for sheet in sheet_list:
        for mod in anchor_modules:
            if mod.sheet_id == sheet:
                ref_list.append(mod.ref)
                break

    alt_list = [('/').join(x[0]) + " ("+ x[1] + ")" for x in zip(sheet_list, ref_list)]
    
    # get the list selection from user
    sheets_for_replication = [sheet_list[i] for i in sheets]

    # now we are ready for replication
    replicator.replicate_layout(pivot_mod, pivot_mod.sheet_id[0:index+1], sheets_for_replication,
                                 containing=containing, remove=remove, tracks=True, zones=True, text=True, drawings=True)

    saved1 = pcbnew.SaveBoard(out_filename, board)
    test_file = out_filename.replace("temp", "test")
    
    return compare_boards.compare_boards(out_filename, test_file)


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "multiple_hierarchy"))
    
    logger.info("Testing multiple hierarchy - inner levels")
    input_file = 'multiple_hierarchy.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp"+".kicad_pcb"
    err = test_file(input_file, output_file, 'Q301', level=1 ,sheets=(0, 2, 5,), containing=False, remove=True)
    assert (err == 0), "multiple_hierarchy - inner levels failed"
    
    logger.info("Testing multiple hierarchy - inner levels pivot on a different level")
    input_file = 'multiple_hierarchy.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp_alt"+".kicad_pcb"
    err = test_file(input_file, output_file, 'Q1401', level=0 ,sheets=(0, 2, 5,), containing=False, remove=True)
    assert (err == 0), "multiple_hierarchy - inner levels from bottom failed"

    logger.info("Testing multiple hierarchy - outer levels")
    input_file = 'multiple_hierarchy_outer.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp"+".kicad_pcb"
    err = test_file(input_file, output_file, 'Q301', level=0 ,sheets=(1,), containing=False, remove=False)
    assert (err == 0), "multiple_hierarchy - outer levels failed"

    print ("all tests passed")

# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='replicate_layout.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Replicate layout plugin version: " + VERSION + " started in standalone mode")

    main()
