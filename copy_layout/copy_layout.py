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
import re
import hashlib
import pickle

Module = namedtuple('Module', ['ref', 'mod', 'mod_id', 'sheet_id', 'filename'])

LayoutData = namedtuple('LayoutData', ['layout', 'hash', 'dict_of_sheets'])

logger = logging.getLogger(__name__)


class Footprint():
    def __init__(self, ref, mod, mod_id, sheet_id, sheetname=None, filename=None):
        self.ref = ref
        self.mod = mod
        self.mod_id = mod_id
        self.sheet_id = sheet_id
        self.sheetname = sheetname
        self.filename = filename

# this function was made by Miles Mccoo
# https://github.com/mmccoo/kicad_mmccoo/blob/master/replicatelayout/replicatelayout.py
def get_coordinate_points_of_shape_poly_set(ps):
    string = ps.Format()
    lines = string.split('\n')
    numpts = int(lines[2])
    pts = [[int(n) for n in x.split(" ")] for x in lines[3:-2]]  # -1 because of the extra two \n
    return pts


def get_module_id(module):
    """ get module id """
    module_path = module.GetPath().split('/')
    module_id = "/".join(module_path[-1:])
    return module_id


def get_sheet_id(module):
    """ get sheet id """
    module_path = module.GetPath().split('/')
    sheet_id = module_path[1:-1]
    return sheet_id


def get_board_modules(board):
    bmod = board.GetModules()
    modules = []
    mod_dict = {}
    for module in bmod:
        mod_named_tuple = Module(mod=module,
                                    mod_id=get_module_id(module),
                                    sheet_id=get_sheet_id(module),
                                    filename="", 
                                    ref=module.GetReference())
        mod_dict[module.GetReference()] = mod_named_tuple
        modules.append(mod_named_tuple)
    return modules


class SchData():
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

    @staticmethod
    def get_sch_hash(sch_file, md5hash):
        # load sch file
        with open(sch_file) as f:
            sch_lines = f.readlines()

        # remove all lines containing references (L, U, AR)
        sch_file_without_reference = [line for line in sch_lines if (not line.startswith("L ")
                                                                     and not line.startswith("F0 ")
                                                                     and not line.startswith("F 0")
                                                                     and not line.startswith("AR ")
                                                                     and not line.startswith("Sheet")
                                                                     and not line.startswith("LIBS:"))]

        # caluclate the hash
        for line in sch_file_without_reference:
            md5hash.update(line)

        return md5hash


class PcbData():
    @staticmethod
    def get_module_id(module):
        """ get module id """
        module_path = module.GetPath().split('/')
        module_id = "/".join(module_path[-1:])
        return module_id

    def get_sheet_id(self, module):
        """ get sheet id """
        module_path = module.GetPath()
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
            pads = mod.mod.PadsList()
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


class SaveLayout():
    def __init__(self, board):
        self.board = board
        self.schematics = SchData(board)
        self.layout = PcbData(board)
        self.layout.set_modules_hierarchy_names(self.schematics.dict_of_sheets)
        # get basic layout info
        pass

    def get_mod_by_ref(self, mod_ref):
        return self.layout.get_mod_by_ref(mod_ref)

    def remove_drawings(self, bounding_box, containing):
        # remove all drawings outside of bounding box
        for drawing in self.board.GetDrawings():
            if not isinstance(drawing, pcbnew.DRAWSEGMENT):
                continue
            drawing_bb = drawing.GetBoundingBox()
            if containing:
                if not bounding_box.Contains(drawing_bb):
                    self.board.RemoveNative(drawing)
            else:
                if bounding_box.Intersects(drawing_bb):
                    self.board.RemoveNative(drawing)

    def remove_text(self, bounding_box, containing):
        # remove all text outside of bounding box
        for text in self.board.GetDrawings():
            if not isinstance(text, pcbnew.TEXTE_PCB):
                continue
            text_bb = text.GetBoundingBox()
            if containing:
                if not bounding_box.Contains(text_bb):
                    self.board.RemoveNative(text)
            else:
                if bounding_box.Intersects(text_bb):
                    self.board.RemoveNative(text)

    def remove_zones(self, bounding_box, containing):
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
        # find all tracks within the pivot bounding box
        all_tracks = self.board.GetTracks()
        # get all the tracks for replication
        for track in all_tracks:
            track_bb = track.GetBoundingBox()
            # if track is contained or intersecting the bounding box
            if containing:
                if not bounding_box.Contains(track_bb):
                    # TODO don't- delete if track is on local nets
                    self.board.RemoveNative(track)
            else:
                if not bounding_box.Intersects(track_bb):
                    # TODO don't- delete if track is on local nets
                    self.board.RemoveNative(track)

    def remove_modules(self, modules):
        for mod in modules:
            self.board.RemoveNative(mod.mod)

    def export_layout(self, mod, level):
        self.pivot_anchor_mod = mod
        # load schematics and calculate hash of schematics (you have to support nested hierarchy)
        list_of_sheet_files = mod.filename[len(level)-1:]

        md5hash = hashlib.md5()
        for sch_file in list_of_sheet_files:
            md5hash = self.schematics.get_sch_hash(sch_file, md5hash)

        hex_hash = md5hash.hexdigest()

        # append hash to new_board filename, so that can be checked on import
        new_file = "_".join(list_of_sheet_files) + "_" + hex_hash + ".kicad_pcb"

        # get modules on a sheet
        modules = self.layout.get_modules_on_sheet(level)
        # the rest
        # get modules bounding box
        bounding_box = self.layout.get_modules_bounding_box(modules)

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

        # save under a new name
        saved = pcbnew.SaveBoard(new_file, self.board)

        # load as text
        with open(new_file, 'r') as f:
            layout = f.read()

        # save all data
        data_to_save = LayoutData(layout, hex_hash, self.schematics.dict_of_sheets)
        # pickle.dump(data_to_save, new_file, pickle.HIGHEST_PROTOCOL)
        data_file = new_file.replace(".kicad_pcb", ".pckl")
        with open(data_file, 'wb') as f:
            pickle.dump(data_to_save, f, 0)

        return os.path.abspath(data_file)        

    def import_layout(self, mod, level, layout_file):
        # load saved design
        with open(layout_file, 'rb') as f:
            data_saved = pickle.load(f)

        self.pivot_anchor_mod = mod
        # load schematics and calculate hash of schematics (you have to support nested hierarchy)
        list_of_sheet_files = mod.filename[len(level)-1:]

        md5hash = hashlib.md5()
        for sch_file in list_of_sheet_files:
            md5hash = self.schematics.get_sch_hash(sch_file, md5hash)

        hex_hash = md5hash.hexdigest()

        # check the hash
        saved_hash = data_saved.hash

        if not saved_hash == hex_hash:
            raise ValueError("Source and destination schematics don't match!")

        # load saved
        temp_filename = 'temp_layout.kicad_pcb'
        with open(temp_filename, 'w') as f:
            f.write(data_saved.layout)

        # restore layout data
        saved_board = pcbnew.LoadBoard(temp_filename)
        saved_layout = PcbData(saved_board)
        saved_layout.set_modules_hierarchy_names(data_saved.dict_of_sheets)

        modules_saved = saved_layout.modules

        modules_to_place = self.layout.get_modules_on_sheet(level)

        if len(modules_to_place) != len(saved_modules):
            raise ValueError("Source and destination footprint count don't match!")

        # sort by ID - I am counting that source and destination sheed have been
        # anotated by KiCad in their final form (reset anotation and then re-anotate)
        modules_to_place = sorted(modules_to_place, key=lambda x: (x.mod_id, x.ref))
        modules_saved = sorted(modules_saved, key=lambda x: (x.mod_id, x.ref))

        # get the saved layout ID numbers and try to figure out a match (at least the same depth, ...)

        a = 2
        pass


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Source_project"))
    source_file = 'multiple_hierarchy.kicad_pcb'

    backup_file = 'multiple_hierarchy.kicad_pcb_bak'

    # create a backup'
    board = pcbnew.LoadBoard(source_file)
    saved = pcbnew.SaveBoard(backup_file, board)
    save_layout = SaveLayout(board)

    pivot_mod_ref = 'Q301'
    pivot_mod = save_layout.get_mod_by_ref(pivot_mod_ref)

    levels = pivot_mod.filename
    # get the level index from user
    index = levels.index(levels[0])

    layout_file = save_layout.export_layout(pivot_mod, pivot_mod.sheetname[0:index+1])

    # restore layout
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Destination_project"))
    destination_file = 'Destination_project.kicad_pcb'
    board = pcbnew.LoadBoard(destination_file)
    restore_layout = SaveLayout(board)

    pivot_mod_ref = 'Q3'
    pivot_mod = restore_layout.get_mod_by_ref(pivot_mod_ref)
    levels = pivot_mod.filename
    # get the level index from user
    index = levels.index(levels[0])

    restore_layout.import_layout(pivot_mod, pivot_mod.sheetname[0:index+1], layout_file)


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