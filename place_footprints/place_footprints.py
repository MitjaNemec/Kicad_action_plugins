# -*- coding: utf-8 -*-
#  place_footprints.py
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
import pcbnew
from collections import namedtuple
import os
import sys
import logging
import itertools
import math
import re

parent_module = sys.modules['.'.join(__name__.split('.')[:-1]) or '__main__']
if __name__ == '__main__' or parent_module.__name__ == '__main__':
    import compare_boards
else:
    from . import compare_boards

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


def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)

SCALE = 1000000.0

Module = namedtuple('Module', ['ref', 'mod', 'mod_id', 'sheet_id', 'filename'])
logger = logging.getLogger(__name__)


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


class Placer():
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

    def get_modules_with_reference_designator(self, ref_des):
        list_of_modules = []
        for m in self.modules:
            for i in range(len(m.ref)):
                if not m.ref[i].isdigit():
                    index = i+1
            m_des = m.ref[:index]
            if m_des == ref_des:
                list_of_modules.append(m.ref)
        return list_of_modules

    def __init__(self, board):
        self.board = board
        self.pcb_filename = os.path.abspath(board.GetFileName())
        self.sch_filename = self.pcb_filename.replace(".kicad_pcb", ".sch")
        self.project_folder = os.path.dirname(self.pcb_filename)

        # get relation between sheetname and it's id
        logger.info('getting project hierarchy from schematics')
        self.dict_of_sheets = self.find_all_sch_files(self.sch_filename, {})

        # check if sheet files dict contains only one item or is empty
        # Most likely cause is that user did not save the schematics file when the plugin was run
        if len(self.dict_of_sheets) <= 1:
            logger.info('getting project hierarchy from schematics')
            raise LookupError("Schematic hierarchy too shallow. You most likely forgot to save the schematcs before running the plugin")

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

        # dobodi vse footprinte z istim ID-jem
        list_of_modules = self.get_list_of_modules_with_same_id(mod.mod_id)
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

        # remove duplicates
        all_sheets.sort()
        all_sheets = list(k for k, _ in itertools.groupby(all_sheets))

        # remove pivot_sheet
        if sheet_id_up_to_level in all_sheets:
            index = all_sheets.index(sheet_id_up_to_level)
            del all_sheets[index]
        logger.info("suitable sheets are:"+repr(all_sheets))
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
            a1 = mod.sheet_id[0:level_depth]
            if level != mod.sheet_id[0:level_depth]:
                modules_not_on_sheet.append(mod)
        return modules_not_on_sheet

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
        height = (bottom-top)/1000000.0
        width = (right-left)/1000000.0
        return height, width

    def get_modules_bounding_box_center(self, modules):
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
        pos_y = (bottom+top)/2
        pos_x = (right+left)/2
        return (pos_x, pos_y)

    def place_circular(self, modules_to_place, reference_footprint, radius, delta_angle):
        logger.info("Starting placing with circular layout")
        # get proper module_list
        modules = []
        for mod_ref in modules_to_place:
            modules.append(self.get_mod_by_ref(mod_ref))

        reference_module = self.get_mod_by_ref(reference_footprint)

        # get first module position
        reference_module_pos = reference_module.mod.GetPosition()
        logger.info("reference module position at: " + repr(reference_module_pos))
        reference_index = modules.index(reference_module)

        point_of_rotation = (reference_module_pos[0], reference_module_pos[1] + radius * SCALE)

        logger.info("rotation center at: " + repr(point_of_rotation))
        for mod in modules:
            index = modules.index(mod)
            delta_index = index - reference_index
            new_position = rotate_around_pivot_point(reference_module_pos, point_of_rotation, delta_index*delta_angle)
            new_position = [int(x) for x in new_position]
            mod.mod.SetPosition(pcbnew.wxPoint(*new_position))

            mod.mod.SetOrientationDegrees(reference_module.mod.GetOrientationDegrees()-delta_index*delta_angle)

            first_mod_flipped = reference_module.mod.IsFlipped()
            if (mod.mod.IsFlipped() != first_mod_flipped):
                flip_module(mod.mod, mod.mod.GetPosition())

    def place_linear(self, modules_to_place, reference_footprint, step_x, step_y):
        logger.info("Starting placing with linear layout")
        # get proper module_list
        modules = []
        for mod_ref in modules_to_place:
            modules.append(self.get_mod_by_ref(mod_ref))

        reference_module = self.get_mod_by_ref(reference_footprint)

        # get reference module position
        reference_module_pos = reference_module.mod.GetPosition()
        reference_index = modules.index(reference_module)

        for mod in modules:
            index = modules.index(mod)
            delta_index = index-reference_index
            new_position = (reference_module_pos.x + delta_index*step_x*SCALE, reference_module_pos.y + delta_index*step_y * SCALE)
            new_position = [int(x) for x in new_position]
            mod.mod.SetPosition(pcbnew.wxPoint(*new_position))

            mod.mod.SetOrientationDegrees(reference_module.mod.GetOrientationDegrees())

            first_mod_flipped = reference_module.mod.IsFlipped()
            if (mod.mod.IsFlipped() != first_mod_flipped):
                flip_module(mod.mod, mod.mod.GetPosition)

    def place_matrix(self, modules_to_place, reference_footprint, step_x, step_y, nr_columns):
        logger.info("Starting placing with matrix layout")
        # get proper module_list
        modules = []
        for mod_ref in modules_to_place:
            modules.append(self.get_mod_by_ref(mod_ref))

        # get first module position
        # TODO - take reference footprint position for start and build matrix around it (before, after)
        first_module = modules[0]
        first_module_pos = first_module.mod.GetPosition()
        for mod in modules[1:]:
            index = modules.index(mod)
            row = index // nr_columns
            column = index - row * nr_columns
            new_pos_x = first_module_pos.x + column * step_x * SCALE
            new_pos_y = first_module_pos.y + row * step_y * SCALE
            new_position = (new_pos_x, new_pos_y)
            new_position = [int(x) for x in new_position]
            mod.mod.SetPosition(pcbnew.wxPoint(*new_position))

            mod.mod.SetOrientationDegrees(first_module.mod.GetOrientationDegrees())

            first_mod_flipped = first_module.mod.IsFlipped()
            if (mod.mod.IsFlipped() != first_mod_flipped):
                flip_module(mod.mod, mod.mod.GetPosition())


def test(in_file, out_file, pivot_module_reference, mode, layout):
    board = pcbnew.LoadBoard(in_file)

    placer = Placer(board)

    if mode == 'by ref':
        module_reference_designator = ''.join(i for i in pivot_module_reference if not i.isdigit())
        module_reference_number = int(''.join(i for i in pivot_module_reference if i.isdigit()))

        # get list of all modules with same reference designator
        list_of_all_modules_with_same_designator = placer.get_modules_with_reference_designator(module_reference_designator)
        sorted_list = natural_sort(list_of_all_modules_with_same_designator)

        list_of_consecutive_modules=[]
        start_index = sorted_list.index(pivot_module_reference)
        count_start = module_reference_number
        for mod in sorted_list[start_index:]:
            if int(''.join(i for i in mod if i.isdigit())) == count_start:
                count_start = count_start + 1
                list_of_consecutive_modules.append(mod)
            else:
                break

        count_start = module_reference_number
        reversed_list = list(reversed(sorted_list))
        start_index = reversed_list.index(pivot_module_reference)
        for mod in reversed_list[start_index:]:
            if int(''.join(i for i in mod if i.isdigit())) == count_start:
                count_start = count_start -1
                list_of_consecutive_modules.append(mod)
            else:
                break

        sorted_modules = natural_sort(list(set(list_of_consecutive_modules)))

    if mode == 'by sheet':
        pivot_module = placer.get_mod_by_ref(pivot_module_reference)
        list_of_modules = placer.get_list_of_modules_with_same_id(pivot_module.mod_id)
        modules = []
        for mod in list_of_modules:
            modules.append(mod.ref)
        sorted_modules = natural_sort(modules)

    reference_module = pivot_module_reference

    if layout == 'circular':
        if mode == 'by sheet':
            placer.place_circular(sorted_modules, reference_module, 10.0, 30.0)
        else:
            placer.place_circular(sorted_modules, reference_module, 10.0, 30.0)
    if layout == 'linear':
        placer.place_linear(sorted_modules, reference_module, 5.0, 0.0)
    if layout == 'matrix':
        placer.place_matrix(sorted_modules, reference_module, 5.0, 5.0, 3)

    saved = pcbnew.SaveBoard(out_file, board)
    test_file = out_file.replace("temp", "test")

    return compare_boards.compare_boards(out_file, test_file)


def main():
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "place_footprints"))
    input_file = 'place_footprints.kicad_pcb'
    pivot_module_reference = 'R202'

    output_file = input_file.split('.')[0]+"_temp_ref_circular"+".kicad_pcb"
    err = test(input_file, output_file, pivot_module_reference, 'by ref', 'circular')
    assert (err == 0), "by reference circular failed"

    output_file = input_file.split('.')[0]+"_temp_ref_linear"+".kicad_pcb"
    err = test(input_file, output_file, pivot_module_reference, 'by ref', 'linear')
    assert (err == 0), "by reference linear failed"

    output_file = input_file.split('.')[0]+"_temp_ref_matrix"+".kicad_pcb"
    err = test(input_file, output_file, pivot_module_reference, 'by ref', 'matrix')
    assert (err == 0), "by reference matrix failed"

    pivot_module_reference = 'R401'
    output_file = input_file.split('.')[0]+"_temp_sheet_circular"+".kicad_pcb"
    err = test(input_file, output_file, pivot_module_reference, 'by sheet', 'circular')
    assert (err == 0), "by sheet circular failed"

    output_file = input_file.split('.')[0]+"_temp_sheet_linear"+".kicad_pcb"
    err = test(input_file, output_file, pivot_module_reference, 'by sheet', 'linear')
    assert (err == 0), "by sheet linear failed"

    output_file = input_file.split('.')[0]+"_temp_sheet_matrix"+".kicad_pcb"
    err = test(input_file, output_file, pivot_module_reference, 'by sheet', 'matrix')
    assert (err == 0), "by sheet matrix failed"

    print ("all tests passed")


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    file_handler = logging.FileHandler(filename='place_footprints.log', mode='w')
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
    logger.info("Place footprints plugin version: " + VERSION + " started in standalone mode")

    main()
