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
    import remove_duplicates
else:
    from . import compare_boards
    from . import remove_duplicates


# V5.1.x backward compatibility for module ID
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


Module = namedtuple('Module', ['ref', 'mod', 'mod_id', 'sheet_id', 'filename'])
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


def rotate_around_center(coordinates, angle):
    """ rotate coordinates for a defined angle in degrees around coordinate center"""
    new_x = coordinates[0] * math.cos(2 * math.pi * angle/360)\
          - coordinates[1] * math.sin(2 * math.pi * angle/360)
    new_y = coordinates[0] * math.sin(2 * math.pi * angle/360)\
          + coordinates[1] * math.cos(2 * math.pi * angle/360)
    return new_x, new_y


def rotate_around_point(old_position, point, angle):
    """ rotate coordinates for a defined angle in degrees around a point """
    # get relative position to point
    rel_x = old_position[0] - point[0]
    rel_y = old_position[1] - point[1]
    # rotate around
    new_rel_x, new_rel_y = rotate_around_center((rel_x, rel_y), angle)
    # get absolute position
    new_position = (new_rel_x + point[0], new_rel_y + point[1])
    return new_position


def get_index_of_tuple(list_of_tuples, index, value):
    for pos, t in enumerate(list_of_tuples):
        if t[index] == value:
            return pos


def get_module_text_items(module):
    """ get all text item belonging to a modules """
    list_of_items = [module.mod.Reference(), module.mod.Value()]

    module_items = module.mod.GraphicalItems()
    for item in module_items:
        if type(item) is pcbnew.TEXTE_MODULE:
            list_of_items.append(item)
    return list_of_items


class Replicator():
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
        module_path = get_path(module).split('/')
        module_id = "/".join(module_path[-1:])
        return module_id

    def get_sheet_id(self, module):
        """ get sheet id """
        module_path = get_path(module).split('/')
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
        self.stage = 1
        self.update_progress = None

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
        for module in bmod:
            mod_named_tuple = Module(mod=module,
                                     mod_id=self.get_module_id(module),
                                     sheet_id=self.get_sheet_id(module)[0],
                                     filename=self.get_sheet_id(module)[1], 
                                     ref=module.GetReference())
            self.modules.append(mod_named_tuple)
        pass

    def get_list_of_modules_with_same_id(self, id):
        list_of_modules = []
        for m in self.modules:
            if m.mod_id == id:
                list_of_modules.append(m)
        return list_of_modules

    def get_sheets_to_replicate(self, mod, level):
        sheet_id = mod.sheet_id
        sheet_file = mod.filename
        # find level path id
        level_file = sheet_file[sheet_id.index(level)]
        logger.info('construcing a list of sheets suitable for replication on level:'+repr(level)+", file:"+repr(level_file))

        src_sheet_path = []
        for i in range(len(sheet_id)):
            src_sheet_path.append(sheet_id[i])
            if sheet_id[i] == level:
                break
        logger.debug("Source sheet path up to the level:" + repr(src_sheet_path))

        # get all footprints with same ID
        list_of_modules = self.get_list_of_modules_with_same_id(mod.mod_id)
        logger.debug("Footprints on the sheets:\n" + repr([x.ref for x in list_of_modules]))

        # log all modules sheet id
        logger.debug("Footprints raw sheet ids:\n" + repr([get_path(x.mod) for x in list_of_modules]))

        # if hierarchy is deeper, match only the sheets with same hierarchy from root to -1
        all_sheets = []

        # go through all footprints with same ID
        for m in list_of_modules:
            # if footprint is on the same file (which should be always)
            if level_file in m.filename:
                sheet_id_list = []
                # construct hierarchy path only up to the level we want
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

        # remove source sheet
        if src_sheet_path in all_sheets:
            index = all_sheets.index(src_sheet_path)
            del all_sheets[index]
        logger.info("All sheets to replicate sorted and without source sheet:\n" + repr(all_sheets))

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

    def get_local_nets(self, src_modules, other_modules):
        # then get nets other modules are connected to
        other_nets = self.get_nets_from_modules(other_modules)
        # then get nets only source modules are connected to
        src_nets = self.get_nets_from_modules(src_modules)

        src_local_nets = []
        for net in src_nets:
            if net not in other_nets:
                src_local_nets.append(net)

        return src_local_nets

    def get_modules_bounding_box(self, modules):
        # get the source bounding box
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
        # find all tracks within the source bounding box
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
        # get all zones in source bounding box
        all_zones = []
        for zoneid in range(self.board.GetAreaCount()):
            all_zones.append(self.board.GetArea(zoneid))
        # find all zones which are completely within the source bounding box
        zones = []
        for zone in all_zones:
            zone_bb = zone.GetBoundingBox()
            if (containing and bounding_box.Contains(zone_bb)) or\
               (not containing and bounding_box.Intersects(zone_bb)):
                zones.append(zone)
        return zones

    def get_text_items(self, bounding_box, containing):
        # get all text objects in source bounding box
        all_text = []
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.TEXTE_PCB):
                continue
            text_bb = drawing.GetBoundingBox()
            if containing:
                if bounding_box.Contains(text_bb):
                    all_text.append(drawing)
            else:
                if bounding_box.Intersects(text_bb):
                    all_text.append(drawing)
        return all_text

    def get_drawings(self, bounding_box, containing):
        # get all drawings in source bounding box
        all_drawings = []
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.DRAWSEGMENT):
                continue
            dwg_bb = drawing.GetBoundingBox()
            if containing:
                if bounding_box.Contains(dwg_bb):
                    all_drawings.append(drawing)
            else:
                if bounding_box.Intersects(dwg_bb):
                    all_drawings.append(drawing)
        return all_drawings

    def get_sheet_anchor_module(self, sheet):
        # get all modules on this sheet
        sheet_modules = self.get_modules_on_sheet(sheet)
        # get anchor module
        list_of_possible_anchor_modules = []
        for mod in sheet_modules:
            if mod.mod_id == self.src_anchor_module.mod_id:
                list_of_possible_anchor_modules.append(mod)

        # if there is only one
        if len(list_of_possible_anchor_modules) == 1:
            sheet_anchor_mod = list_of_possible_anchor_modules[0]
        # if there are more then one, we're dealing with multiple hierarchy
        # the correct one is the one who's path is the best match
        else:
            list_of_mathces = []
            for mod in list_of_possible_anchor_modules:
                index = list_of_possible_anchor_modules.index(mod)
                matches = 0
                for item in self.src_anchor_module.sheet_id:
                    if item in mod.sheet_id:
                        matches = matches + 1
                list_of_mathces.append((index, matches))
            # select the one with most matches
            index, _ = max(list_of_mathces, key=lambda item: item[1])
            sheet_anchor_mod = list_of_possible_anchor_modules[index]
        return sheet_anchor_mod

    def get_net_pairs(self, sheet):
        """ find all net pairs between source sheet and current sheet"""
        # find all modules, pads and nets on this sheet
        sheet_modules = self.get_modules_on_sheet(sheet)

        # find all net pairs via same modules pads,
        net_pairs = []
        net_dict = {}
        # construct module pairs
        mod_matches = []
        for s_mod in self.src_modules:
            mod_matches.append([s_mod.mod, s_mod.mod_id, s_mod.sheet_id])

        for d_mod in sheet_modules:
            for mod in mod_matches:
                if mod[1] == d_mod.mod_id:
                    index = mod_matches.index(mod)
                    mod_matches[index].append(d_mod.mod)
                    mod_matches[index].append(d_mod.mod_id)
                    mod_matches[index].append(d_mod.sheet_id)
        # find closest match
        mod_pairs = []
        mod_pairs_by_reference = []
        for index in range(len(mod_matches)):
            mod = mod_matches[index]
            # get number of matches
            matches = (len(mod) - 3) // 3
            # if more than one match, get the most likely one
            # this is when replicating a sheet which consist of two or more identical subsheets (multiple hierachy)
            # todo might want to find common code with code in "get_sheet_anchor_module"
            if matches > 1:
                match_len = []
                for index in range(0, matches):
                    match_len.append(len(set(mod[2]) & set(mod[2+3*(index+1)])))
                index = match_len.index(max(match_len))
                mod_pairs.append((mod[0], mod[3*(index+1)]))
                mod_pairs_by_reference.append((mod[0].GetReference(), mod[3*(index+1)].GetReference()))
            # if only one match
            elif matches == 1:
                mod_pairs.append((mod[0], mod[3]))
                mod_pairs_by_reference.append((mod[0].GetReference(), mod[3].GetReference()))
            # can not find at least one matching footprint
            elif matches == 0:
                raise LookupError("Could not find at least one matching footprint for: " + mod[0].GetReference() +
                                  ".\nPlease make sure that schematics and layout are in sync.")

        pad_pairs = []
        for x in range(len(mod_pairs)):
            pad_pairs.append([])

        for pair in mod_pairs:
            index = mod_pairs.index(pair)
            # get all footprint pads
            s_mod_pads = pair[0].Pads()
            d_mod_pads = pair[1].Pads()
            # create a list of padsnames and pads
            s_pads = []
            d_pads = []
            for pad in s_mod_pads:
                s_pads.append((pad.GetName(), pad))
            for pad in d_mod_pads:
                d_pads.append((pad.GetName(), pad))
            # sort by padnames
            s_pads.sort(key=lambda tup: tup[0])
            d_pads.sort(key=lambda tup: tup[0])
            # extract pads and append them to pad pairs list
            pad_pairs[index].append([x[1] for x in s_pads])
            pad_pairs[index].append([x[1] for x in d_pads])

        for pair in mod_pairs:
            index = mod_pairs.index(pair)
            s_mod = pair[0]
            d_mod = pair[1]
            # get their pads
            s_mod_pads = pad_pairs[index][0]
            d_mod_pads = pad_pairs[index][1]
            # I am going to assume pads are in the same order
            s_nets = []
            d_nets = []
            # get nelists for each pad
            for p_pad in s_mod_pads:
                pad_name = p_pad.GetName()
                s_nets.append((pad_name, p_pad.GetNetname()))
            for s_pad in d_mod_pads:
                pad_name = s_pad.GetName()
                d_nets.append((pad_name, s_pad.GetNetname()))
                net_dict[s_pad.GetNetname()] = s_pad.GetNet()
            # sort both lists by pad name
            # so that they have the same order - needed in some cases
            # as the iterator thorugh the pads list does not return pads always in the proper order
            s_nets.sort(key=lambda tup: tup[0])
            d_nets.sort(key=lambda tup: tup[0])
            # build list of net tupules
            for net in s_nets:
                index = get_index_of_tuple(s_nets, 1, net[1])
                net_pairs.append((s_nets[index][1], d_nets[index][1]))

        # remove duplicates
        net_pairs_clean = list(set(net_pairs))

        return net_pairs_clean, net_dict

    def prepare_for_replication(self, level, containing):
        # get a list of source modules for replication
        logger.info("Getting the list of source footprints")
        self.update_progress(self.stage, 0/8, None)
        self.src_modules = self.get_modules_on_sheet(level)
        # get the rest of the modules
        logger.info("Getting the list of all the remaining footprints")
        self.update_progress(self.stage, 1/8, None)
        self.other_modules = self.get_modules_not_on_sheet(level)
        # get nets local to source modules
        logger.info("Getting nets local to source footprints")
        self.update_progress(self.stage, 2/8, None)
        self.src_local_nets = self.get_local_nets(self.src_modules, self.other_modules)
        # get source bounding box
        logger.info("Getting source bounding box")
        self.update_progress(self.stage, 3/8, None)
        self.src_bounding_box = self.get_modules_bounding_box(self.src_modules)
        # get source tracks
        logger.info("Getting source tracks")
        self.update_progress(self.stage, 4/8, None)
        self.src_tracks = self.get_tracks(self.src_bounding_box, self.src_local_nets, containing)
        # get source zones
        logger.info("Getting source zones")
        self.update_progress(self.stage, 5/8, None)
        self.src_zones = self.get_zones(self.src_bounding_box, containing)
        # get source text items
        logger.info("Getting source text items")
        self.update_progress(self.stage, 6/8, None)
        self.src_text = self.get_text_items(self.src_bounding_box, containing)
        # get source drawings
        logger.info("Getting source text items")
        self.update_progress(self.stage, 7/8, None)
        self.src_drawings = self.get_drawings(self.src_bounding_box, containing)
        self.update_progress(self.stage, 8/8, None)

    def replicate_modules(self):
        logger.info("Replicating footprints")
        nr_sheets = len(self.dst_sheets)
        for st_index in range(nr_sheets):
            sheet = self.dst_sheets[st_index]
            progress = st_index/nr_sheets
            self.update_progress(self.stage, progress, None)
            logger.info("Replicating footprints on sheet " + repr(sheet))
            # get anchor module
            dst_anchor_module = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to source module
            dst_anchor_module_angle = dst_anchor_module.mod.GetOrientationDegrees()
            # get exact anchor position
            dst_anchor_module_position = dst_anchor_module.mod.GetPosition()

            anchor_delta_angle = self.src_anchor_module.mod.GetOrientationDegrees() - dst_anchor_module_angle
            anchor_delta_pos = dst_anchor_module_position - self.src_anchor_module.mod.GetPosition()

            # go through all modules
            dst_modules = self.get_modules_on_sheet(sheet)
            nr_mods = len(dst_modules)
            for mod_index in range(nr_mods):
                dst_mod = dst_modules[mod_index]

                progress = progress + (1/nr_sheets)*(1/nr_mods)
                self.update_progress(self.stage, progress, None)

                # skip locked footprints
                if dst_mod.mod.IsLocked() is True and self.rep_locked is False:
                    continue

                # find proper match in source modules
                src_mod = None
                list_of_possible_src_modules = []
                for s_mod in self.src_modules:
                    if s_mod.mod_id == dst_mod.mod_id:
                        list_of_possible_src_modules.append(s_mod)

                # if there is more than one possible anchor, select the correct one
                if len(list_of_possible_src_modules) == 1:
                    src_mod = list_of_possible_src_modules[0]
                else:
                    list_of_matches = []
                    for m in list_of_possible_src_modules:
                        index = list_of_possible_src_modules.index(m)
                        matches = 0
                        for item in dst_mod.sheet_id:
                            if item in m.sheet_id:
                                matches = matches + 1
                        list_of_matches.append((index, matches))
                    # select the one with most matches
                    index, _ = max(list_of_matches, key=lambda item: item[1])
                    src_mod = list_of_possible_src_modules[index]

                # get module to clone position
                src_module_orientation = src_mod.mod.GetOrientationDegrees()
                src_module_position = src_mod.mod.GetPosition()
                # get relative position with respect to source anchor
                src_anchor_position = self.src_anchor_module.mod.GetPosition()
                src_mod_delta_position = src_module_position - src_anchor_position

                # new orientation is simple
                new_orientation = src_module_orientation - anchor_delta_angle
                old_position = src_mod_delta_position + dst_anchor_module_position
                newposition = rotate_around_point(old_position, dst_anchor_module_position, anchor_delta_angle)

                # convert to tuple of integers
                newposition = [int(x) for x in newposition]
                # place current module - only if current module is not also the anchor
                if dst_mod.ref != dst_anchor_module.ref:
                    dst_mod.mod.SetPosition(pcbnew.wxPoint(*newposition))

                    src_mod_flipped = src_mod.mod.IsFlipped()
                    if dst_mod.mod.IsFlipped() != src_mod_flipped:
                        flip_module(dst_mod.mod, dst_mod.mod.GetPosition())
                        # dst_mod.mod.Flip(dst_mod.mod.GetPosition())
                    dst_mod.mod.SetOrientationDegrees(new_orientation)

                    # Copy local settings.
                    dst_mod.mod.SetLocalClearance(src_mod.mod.GetLocalClearance())
                    dst_mod.mod.SetLocalSolderMaskMargin(src_mod.mod.GetLocalSolderMaskMargin())
                    dst_mod.mod.SetLocalSolderPasteMargin(src_mod.mod.GetLocalSolderPasteMargin())
                    dst_mod.mod.SetLocalSolderPasteMarginRatio(src_mod.mod.GetLocalSolderPasteMarginRatio())
                    dst_mod.mod.SetZoneConnection(src_mod.mod.GetZoneConnection())

                # replicate also text layout - also for anchor module. I am counting that the user is lazy and will
                # just position the anchors and will not edit them
                # get source_module_text
                # get module text
                src_mod_text_items = get_module_text_items(src_mod)
                dst_mod_text_items = get_module_text_items(dst_mod)
                # check if both modules (source and the one for replication) have the same number of text items
                if len(src_mod_text_items) != len(dst_mod_text_items):
                    raise LookupError("Source module: " + src_mod.ref + " has different number of text items (" + repr(len(src_mod_text_items))
                                      + ")\nthan module for replication: " + dst_mod.ref + " (" + repr(len(dst_mod_text_items)) + ")")
                # replicate each text item
                for src_text in src_mod_text_items:
                    index = src_mod_text_items.index(src_text)
                    src_text_position = src_text.GetPosition() + anchor_delta_pos

                    newposition = rotate_around_point(src_text_position, dst_anchor_module_position, anchor_delta_angle)

                    # convert to tuple of integers
                    newposition = [int(x) for x in newposition]
                    dst_mod_text_items[index].SetPosition(pcbnew.wxPoint(*newposition))

                    # set orientation
                    dst_mod_text_items[index].SetTextAngle(src_text.GetTextAngle())
                    # thickness
                    dst_mod_text_items[index].SetThickness(src_text.GetThickness())
                    # width
                    dst_mod_text_items[index].SetTextWidth(src_text.GetTextWidth())
                    # height
                    dst_mod_text_items[index].SetTextHeight(src_text.GetTextHeight())
                    # rest of the parameters
                    # TODO check SetEffects method, might be better
                    dst_mod_text_items[index].SetItalic(src_text.IsItalic())
                    dst_mod_text_items[index].SetBold(src_text.IsBold())
                    dst_mod_text_items[index].SetMirrored(src_text.IsMirrored())
                    dst_mod_text_items[index].SetMultilineAllowed(src_text.IsMultilineAllowed())
                    dst_mod_text_items[index].SetHorizJustify(src_text.GetHorizJustify())
                    dst_mod_text_items[index].SetVertJustify(src_text.GetVertJustify())
                    dst_mod_text_items[index].SetKeepUpright(src_text.IsKeepUpright())
                    # set visibility
                    dst_mod_text_items[index].SetVisible(src_text.IsVisible())

    def replicate_tracks(self):
        logger.info("Replicating tracks")
        nr_sheets = len(self.dst_sheets)
        for st_index in range(nr_sheets):
            sheet = self.dst_sheets[st_index]
            progress = st_index/nr_sheets
            self.update_progress(self.stage, progress, None)
            logger.info("Replicating tracks on sheet " + repr(sheet))

            # get anchor module
            dst_anchor_module = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to source anchor module
            dst_anchor_module_angle = dst_anchor_module.mod.GetOrientation()
            # get exact anchor position
            dst_anchor_module_position = dst_anchor_module.mod.GetPosition()

            src_anchor_module_angle = self.src_anchor_module.mod.GetOrientation()
            src_anchor_module_position = self.src_anchor_module.mod.GetPosition()

            move_vector = dst_anchor_module_position - src_anchor_module_position
            delta_orientation = dst_anchor_module_angle - src_anchor_module_angle

            net_pairs, net_dict = self.get_net_pairs(sheet)

            # go through all the tracks
            nr_tracks = len(self.src_tracks)
            for track_index in range(nr_tracks):
                track = self.src_tracks[track_index]
                progress = progress + (1/nr_sheets)*(1/nr_tracks)
                self.update_progress(self.stage, progress, None)
                # get from which net we are cloning
                from_net_name = track.GetNetname()
                # find to net
                tup = [item for item in net_pairs if item[0] == from_net_name]
                # if net was not found, then the track is not part of this sheet and should not be cloned
                if not tup:
                    pass
                else:
                    to_net_name = tup[0][1]
                    to_net_code = net_dict[to_net_name].GetNet()
                    to_net_item = net_dict[to_net_name]

                    # make a duplicate, move it, rotate it, select proper net and add it to the board
                    new_track = track.Duplicate()
                    new_track.Rotate(src_anchor_module_position, delta_orientation)
                    new_track.Move(move_vector)
                    new_track.SetNetCode(to_net_code)
                    new_track.SetNet(to_net_item)
                    self.board.Add(new_track)

    def replicate_zones(self):
        """ method which replicates zones"""
        logger.info("Replicating zones")
        # start cloning
        nr_sheets = len(self.dst_sheets)
        for st_index in range(nr_sheets):
            sheet = self.dst_sheets[st_index]
            progress = st_index/nr_sheets
            self.update_progress(self.stage, progress, None)
            logger.info("Replicating zones on sheet " + repr(sheet))

            # get anchor module
            dst_anchor_module = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to source anchor module
            dst_anchor_module_angle = dst_anchor_module.mod.GetOrientation()
            # get exact anchor position
            dst_anchor_module_position = dst_anchor_module.mod.GetPosition()

            src_anchor_module_angle = self.src_anchor_module.mod.GetOrientation()
            src_anchor_module_position = self.src_anchor_module.mod.GetPosition()

            move_vector = dst_anchor_module_position - src_anchor_module_position
            delta_orientation = dst_anchor_module_angle - src_anchor_module_angle

            net_pairs, net_dict = self.get_net_pairs(sheet)
            # go through all the zones
            nr_zones = len(self.src_zones)
            for zone_index in range(nr_zones):
                zone = self.src_zones[zone_index]
                progress = progress + (1/nr_sheets)*(1/nr_zones)
                self.update_progress(self.stage, progress, None)

                # get from which net we are cloning
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
                    to_net_code = 0
                    to_net_item = self.board.FindNet(0)
                else:
                    to_net_code = net_dict[to_net_name].GetNet()
                    to_net_item = net_dict[to_net_name]

                # make a duplicate, move it, rotate it, select proper net and add it to the board
                new_zone = zone.Duplicate()
                new_zone.Rotate(src_anchor_module_position, delta_orientation)
                new_zone.Move(move_vector)
                new_zone.SetNetCode(to_net_code)
                new_zone.SetNet(to_net_item)
                self.board.Add(new_zone)

    def replicate_text(self):
        logger.info("Replicating text")
        # start cloning
        nr_sheets = len(self.dst_sheets)
        for st_index in range(nr_sheets):
            sheet = self.dst_sheets[st_index]
            progress = st_index/nr_sheets
            self.update_progress(self.stage, progress, None)
            logger.info("Replicating text on sheet " + repr(sheet))

            # get anchor module
            dst_anchor_module = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to source module
            dst_anchor_module_angle = dst_anchor_module.mod.GetOrientationDegrees()
            # get exact anchor position
            dst_anchor_module_position = dst_anchor_module.mod.GetPosition()

            anchor_delta_angle = self.src_anchor_module.mod.GetOrientationDegrees() - dst_anchor_module_angle
            anchor_delta_pos = dst_anchor_module_position - self.src_anchor_module.mod.GetPosition()

            nr_text = len(self.src_text)
            for text_index in range(nr_text):
                text = self.src_text[text_index]
                progress = progress + (1/nr_sheets)*(1/nr_text)
                self.update_progress(self.stage, progress, None)

                new_text = text.Duplicate()
                new_text.Move(anchor_delta_pos)
                new_text.Rotate(dst_anchor_module_position, -anchor_delta_angle * 10)
                self.board.Add(new_text)

    def replicate_drawings(self):
        logger.info("Replicating drawings")
        nr_sheets = len(self.dst_sheets)
        for st_index in range(nr_sheets):
            sheet = self.dst_sheets[st_index]
            progress = st_index/nr_sheets
            self.update_progress(self.stage, progress, None)
            logger.info("Replicating drawings on sheet " + repr(sheet))

            # get anchor module
            dst_anchor_module = self.get_sheet_anchor_module(sheet)
            # get anchor angle with respect to source module
            dst_anchor_module_angle = dst_anchor_module.mod.GetOrientationDegrees()
            # get exact anchor position
            dst_anchor_module_position = dst_anchor_module.mod.GetPosition()

            anchor_delta_angle = self.src_anchor_module.mod.GetOrientationDegrees() - dst_anchor_module_angle
            anchor_delta_pos = dst_anchor_module_position - self.src_anchor_module.mod.GetPosition()

            # go through all the drawings
            nr_drawings = len(self.src_drawings)
            for dw_index in range(nr_drawings):
                drawing = self.src_drawings[dw_index]
                progress = progress + (1/nr_sheets)*(1/nr_drawings)
                self.update_progress(self.stage, progress, None)

                new_drawing = drawing.Duplicate()
                new_drawing.Move(anchor_delta_pos)
                new_drawing.Rotate(dst_anchor_module_position, -anchor_delta_angle * 10)

                self.board.Add(new_drawing)

    def remove_zones_tracks(self, containing):
        for index in range(len(self.dst_sheets)):
            sheet = self.dst_sheets[index]
            self.update_progress(self.stage, index / len(self.dst_sheets), None)
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
                # minus the tracks in source bounding box
                if track not in self.src_tracks:
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
                # minus the zones in source bounding box
                if zone not in self.src_zones:
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
                # ignore text in the source sheet
                if drawing in self.src_text:
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
                # ignore text in the source sheet
                if drawing in self.src_drawings:
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

    def removing_duplicates(self):
        remove_duplicates.remove_duplicates(self.board)

    def replicate_layout(self, src_anchor_module, level, dst_sheets,
                         containing, remove, tracks, zones, text, drawings, rm_duplicates, rep_locked):
        logger.info( "Starting replication of sheets: " + repr(dst_sheets)
                     +"\non level: " + repr(level)
                     +"\nwith tracks=" + repr(tracks) +", zone=" + repr(zones) +", text=" + repr(text)
                     +", containing=" + repr(containing) +", remove=" + repr(remove) +", locked=" + repr(rep_locked))

        self.level = level
        self.src_anchor_module = src_anchor_module
        self.dst_sheets = dst_sheets
        self.rep_locked = rep_locked

        if remove:
            self.max_stages = 2
        else:
            self.max_stages = 0
        if tracks:
            self.max_stages = self.max_stages + 1
        if zones:
            self.max_stages = self.max_stages + 1
        if text:
            self.max_stages = self.max_stages + 1
        if drawings:
            self.max_stages = self.max_stages + 1
        if rm_duplicates:
            self.max_stages = self.max_stages + 1

        # get source anchor module details
        self.src_anchor_module_angle = self.src_anchor_module.mod.GetOrientationDegrees()
        self.src_anchor_module_position = self.src_anchor_module.mod.GetPosition()
        self.update_progress(self.stage, 0.0, "Preparing for replication")
        self.prepare_for_replication(level, containing)
        if remove:
            logger.info("Removing tracks and zones, before module placement")
            self.stage = 2
            self.update_progress(self.stage, 0.0, "Removing zones and tracks")
            self.remove_zones_tracks(containing)
        self.stage = 3
        self.update_progress(self.stage, 0.0, "Replicating footprints")
        self.replicate_modules()
        if remove:
            logger.info("Removing tracks and zones, after module placement")
            self.stage = 4
            self.update_progress(self.stage, 0.0, "Removing zones and tracks")
            self.remove_zones_tracks(containing)
        if tracks:
            self.stage = 5
            self.update_progress(self.stage, 0.0, "Replicating tracks")
            self.replicate_tracks()
        if zones:
            self.stage = 6
            self.update_progress(self.stage, 0.0, "Replicating zones")
            self.replicate_zones()
        if text:
            self.stage = 7
            self.update_progress(self.stage, 0.0, "Replicating text")
            self.replicate_text()
        if drawings:
            self.stage = 8
            self.update_progress(self.stage, 0.0, "Replicating drawings")
            self.replicate_drawings()
        if rm_duplicates:
            self.stage = 9
            self.update_progress(self.stage, 0.0, "Removing duplicates")
            self.removing_duplicates()
        # finally at the end refill the zones
        filler = pcbnew.ZONE_FILLER(self.board)
        filler.Fill(self.board.Zones())


def update_progress(stage, percentage, message=None):
    if message is not None:
        print(message)
    print(percentage)


def test_file(in_filename, out_filename, src_anchor_module_reference, level, sheets, containing, remove):
    board = pcbnew.LoadBoard(in_filename)
    # get board information
    replicator = Replicator(board)
    # get source module info
    src_anchor_module = replicator.get_mod_by_ref(src_anchor_module_reference)
    # have the user select replication level
    levels = src_anchor_module.filename
    # get the level index from user
    index = levels.index(levels[level])
    # get list of sheets
    sheet_list = replicator.get_sheets_to_replicate(src_anchor_module, src_anchor_module.sheet_id[index])

    # get anchor modules
    anchor_modules = replicator.get_list_of_modules_with_same_id(src_anchor_module.mod_id)
    # find matching anchors to matching sheets
    ref_list = []
    for sheet in sheet_list:
        for mod in anchor_modules:
            if mod.sheet_id == sheet:
                ref_list.append(mod.ref)
                break

    # get the list selection from user
    dst_sheets = [sheet_list[i] for i in sheets]

    # first get all the anchor footprints
    all_sheet_footprints = []
    for sheet in dst_sheets:
        all_sheet_footprints.extend(replicator.get_modules_on_sheet(sheet))
    anchor_fp = [x for x in all_sheet_footprints if x.mod_id == src_anchor_module.mod_id]
    if all(src_anchor_module.mod.IsFlipped() == dst_mod.mod.IsFlipped() for dst_mod in anchor_fp):
        a = 2
    else:
        assert(2==3), "Destination anchor footprints are not on the same layer as source anchor footprint"

    # now we are ready for replication
    replicator.update_progress = update_progress
    replicator.replicate_layout(src_anchor_module, src_anchor_module.sheet_id[0:index+1], dst_sheets,
                                containing=containing, remove=remove, rm_duplicates=True,
                                tracks=True, zones=True, text=True, drawings=True, rep_locked=True)

    pcbnew.SaveBoard(out_filename, board)
    test_filename = out_filename.replace("temp", "test")

    return compare_boards.compare_boards(out_filename, test_filename)


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "multiple_hierarchy"))
    
    logger.info("Testing multiple hierarchy - inner levels")
    input_file = 'multiple_hierarchy.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp"+".kicad_pcb"
    err = test_file(input_file, output_file, 'Q301', level=1, sheets=(0, 2, 5,), containing=False, remove=True)
    assert (err == 0), "multiple_hierarchy - inner levels failed"
    
    logger.info("Testing multiple hierarchy - inner levels source on a different hierarchical level")
    input_file = 'multiple_hierarchy.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp_alt"+".kicad_pcb"
    err = test_file(input_file, output_file, 'Q1401', level=0, sheets=(0, 2, 5,), containing=False, remove=True)
    assert (err == 0), "multiple_hierarchy - inner levels from bottom failed"

    logger.info("Testing multiple hierarchy - outer levels")
    input_file = 'multiple_hierarchy_outer.kicad_pcb'
    output_file = input_file.split('.')[0]+"_temp"+".kicad_pcb"
    err = test_file(input_file, output_file, 'Q301', level=0, sheets=(1,), containing=False, remove=False)
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
    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("Replicate layout plugin version: " + VERSION + " started in standalone mode")

    main()
