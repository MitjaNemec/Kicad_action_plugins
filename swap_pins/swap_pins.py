#  action_swap_pins.py
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
from __future__ import absolute_import, division, print_function
import pcbnew
import os
import math
from operator import itemgetter
import re
import logging
import sys

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


def str_diff(str1, str2):
    num_diffs = 0
    diff_str = ""
    for a, b in zip(str1, str2):
        if a != b:
            num_diffs = num_diffs + 1
            diff_str = diff_str + a
    return num_diffs, diff_str


def swap(board, pad_1, pad_2):
    logger.info("Starting swap_pins")

    # get all file paths
    pcb_file = os.path.abspath(str(board.GetFileName()))
    sch_file = os.path.abspath(str(board.GetFileName()).replace(".kicad_pcb", ".sch"))
    cache_file = os.path.abspath(str(board.GetFileName()).replace(".kicad_pcb", "-cache.lib"))

    logger.info("main sch file is: " + sch_file)
    logger.info("main pcb file is: " + pcb_file)
    logger.info("sch cache file is: " + cache_file)

    # get pad numbers
    pad_nr_1 = pad_1.GetPadName()
    pad_nr_2 = pad_2.GetPadName()
    net_1 = pad_1.GetNet()
    net_2 = pad_2.GetNet()
    net_name_1 = net_1.GetNetname().split('/')[-1]
    net_name_2 = net_2.GetNetname().split('/')[-1]

    # get module reference
    footprint_reference = pad_2.GetParent().GetReference()

    logger.info("Swaping pins: " + pad_nr_1 + ", " + pad_nr_2 +
                " on: " + footprint_reference + " on nets: " + net_name_1 + ", " + net_name_2)

    # get all schematic pages
    all_sch_files = []
    all_sch_files = find_all_sch_files(sch_file, all_sch_files)
    all_sch_files = list(set(all_sch_files))

    logger.info("All schematics files are:\n" + "\n".join(all_sch_files))

    # find symbol location (in which file and where in canvas)
    relevant_sch_files = []
    for page in all_sch_files:
        # link refernce to symbol
        with open(page, 'rb') as f:
            contents = f.read().decode('utf-8')
            # go through all components
            comp_indices = [m.start() for m in re.finditer('\$Comp', contents)]
            endcomp_indices = [m.start() for m in re.finditer('\$EndComp', contents)]

            if len(comp_indices) != len(endcomp_indices):
                raise LookupError("Schematic page contains errors")

            component_locations = zip(comp_indices, endcomp_indices)
            for comp_location in component_locations:
                component_reference = contents[comp_location[0]:comp_location[1]].split('\n')
                symbol_name = None
                sym_name_temp = None
                for line in component_reference:
                    # if there is no multiple hierarchy there is only one reference
                    # and it is in the line starting with "L "
                    if line.startswith('L '):
                        sym_name_temp = line.split()[1]
                        if line.split()[2] == footprint_reference:
                            symbol_name = sym_name_temp
                    # if there are multiple hierachic pages, there are multiple references
                    # stored in line starting with "AR "
                    if line.startswith('AR '):
                        if line.split()[2].split("\"")[1] == footprint_reference:
                            symbol_name = sym_name_temp

                if symbol_name is not None:
                    for line in component_reference:
                        if line.startswith('U '):
                            symbol_unit = line.split()[1]
                        if line.startswith('P '):
                            symbol_loc = (line.split()[1], line.split()[2])
                            relevant_sch_files.append((page, symbol_unit, symbol_loc, symbol_name))
                            logger.info(symbol_name + " unit: " + symbol_unit + " present on page: " + page)
                            break

    # if no symbol has been found raise an expcetion
    if not relevant_sch_files:
        logger.info("No coresponding symbols found in the schematics")
        raise LookupError("No coresponding symbols found in the schematics")

    # load the symbol from cache library
    logger.info("Looking for: %s in cache.lib" % relevant_sch_files[0][3])
    with open(cache_file, 'rb') as f:
        contents = f.read().decode('utf-8')
        def_indices = [m.start() for m in re.finditer('DEF ', contents)]
        enddef_indices = [m.start() for m in re.finditer('ENDDEF', contents)]
        if len(def_indices) != len(enddef_indices):
            logger.info("Cache library contains errors")
            raise LookupError("Cache library contains errors")
        symbol_locations = zip(def_indices, enddef_indices)
        # go through all the symbols in the library
        symbol = None
        for sym_location in symbol_locations:
            sym = contents[sym_location[0]:sym_location[1]].split('\n')
            # go throguh all lines in the symbol and find a match
            for line in sym:
                if line.startswith('DEF '):
                    cache_sym_name = line.split()[1]
                    sch_sym_name = relevant_sch_files[0][3]
                    num, diff = str_diff(cache_sym_name, sch_sym_name)
                    # support old and new style of cache symbol entry (undersore or colon)
                    if (num == 1 and diff == "_") or num == 0:
                        # found a match, break from both loops
                        symbol = sym
                        logger.info("Found symbol in cache library")
                        break
            else:
                # Continue if the inner loop wasn't broken.
                continue
            # Inner loop was broken, break the outer.
            break
        # here I should test if symbol was found
        if symbol is None:
            logger.info("Did not find symbol in the cache library. Cache library is not fresh")
            raise LookupError("Did not find symbol in the cache library. Cache library is not fresh")

    # get the number of units
    for field in symbol:
        if field.startswith('DEF '):
            nr_units = int(field.split()[7])
            logger.info("Symbol has " + str(nr_units) + " units")
            break

    # grab the pins
    symbol_pins = []
    for field in symbol:
        if field.startswith('X '):
            symbol_pins.append(tuple(field.split()))

    # select only relevant pins
    relevant_pins = [(), ()]
    for pin in symbol_pins:
        if pin[2] == pad_nr_1:
            relevant_pins[0] = pin
        if pin[2] == pad_nr_2:
            relevant_pins[1] = pin

    logger.info("Relevant pins are: name: " + relevant_pins[0][1] + ", number: " + relevant_pins[0][2] + "; " +
                                   "name: " + relevant_pins[1][1] + ", number: " + relevant_pins[1][2])

    unit_1 = relevant_pins[0][9]
    unit_2 = relevant_pins[1][9]

    # check wheather any of the pins to swap are marked as common pins in multi unit symbol
    if unit_1 == "0" or unit_2 == "0":
        logger.info("Swapping common pins of multi unit symbol is not supported!\n" +
                     "If the symbol has single unit, there is an error in symbol pin definitions!")
        raise ValueError("Swapping common pins of multi unit symbol is not supported!\n" +
                         "If the symbol has single unit, there is an error in symbol pin definitions!")

    logger.info("Relevant pins are on units: " + unit_1 + ", " + unit_2)

    # get the pages of correcsponding unit
    page_1 = [x for x in relevant_sch_files if x[1] == unit_1][0][0]
    page_1_loc = [x for x in relevant_sch_files if x[1] == unit_1][0][2]
    page_2 = [x for x in relevant_sch_files if x[1] == unit_2][0][0]
    page_2_loc = [x for x in relevant_sch_files if x[1] == unit_2][0][2]

    logger.info("Unit 1 on page: " + page_1 +
                " at: " + str(page_1_loc[0]) + ", " + str(page_1_loc[1]))
    logger.info("Unit 2 on page: " + page_2 +
                " at: " + str(page_2_loc[0]) + ", " + str(page_2_loc[1]))

    # get pin locations within schematics
    pin_1_loc = (str(int(page_1_loc[0]) + int(relevant_pins[0][3])), str(int(page_1_loc[1]) - int(relevant_pins[0][4])))
    pin_2_loc = (str(int(page_2_loc[0]) + int(relevant_pins[1][3])), str(int(page_2_loc[1]) - int(relevant_pins[1][4])))

    logger.info("Pin 1 at: " + str(pin_1_loc[0]) + ", " + str(pin_1_loc[1]))
    logger.info("Pin 2 at: " + str(pin_2_loc[0]) + ", " + str(pin_2_loc[1]))

    # get pin orientation in the symbol U=3 R=0 D=1 L=2
    pin_1_rot = relevant_pins[0][6]
    pin_2_rot = relevant_pins[1][6]
    if pin_1_rot == 'R':
        pin_1_rot = '0'
    elif pin_1_rot == 'D':
        pin_1_rot = '1'
    elif pin_1_rot == 'L':
        pin_1_rot = '2'
    elif pin_1_rot == 'U':
        pin_1_rot = '3'
    if pin_2_rot == 'R':
        pin_2_rot = '0'
    elif pin_2_rot == 'D':
        pin_2_rot = '1'
    elif pin_2_rot == 'L':
        pin_2_rot = '2'
    elif pin_2_rot == 'U':
        pin_2_rot = '3'

    logger.info("Pin 1 rotation: " + pin_1_rot)
    logger.info("Pin 2 rotation: " + pin_2_rot)

    # load schematics
    with open(page_1, 'rb') as f:
        file_contents = f.read().decode('utf-8')
        shematics_1 = file_contents.split('\n')
    # parse it and find text labels at pin locations
    list_line_1 = []
    for index, line in enumerate(shematics_1):
        if line.startswith('Text '):
            line_fields = line.split()
            if line_fields[1] == 'Label' or line_fields[1] == 'GLabel' or line_fields[1] == 'HLabel':
                line_index_1 = index
                next_line_1 = shematics_1[line_index_1 + 1]
                # if label is precisely at pin location
                if line_fields[2] == pin_1_loc[0] and line_fields[3] == pin_1_loc[1]:
                    list_line_1.append((line, next_line_1, line_index_1, 0.0))
                    logger.info("Found label at pin 1")
                # or if label text matches the net name and is close enoght
                # TODO if the label does not match the net name then we have a problem
                if next_line_1.rstrip() == net_name_1:
                    label_location = (line_fields[2], line_fields[3])
                    distance = get_distance(pin_1_loc, label_location)
                    list_line_1.append((line, next_line_1, line_index_1, distance))
                    logger.info("Found label near pin 1")

    # remove duplicates
    list_line_1 = list(set(list_line_1))
    logger.info("list_line_1="+repr(list_line_1))
    # find closest label
    if len(list_line_1) == 0:
        line_1 = None
    if len(list_line_1) == 1:
        line_1 = list_line_1[0]
    if len(list_line_1) > 1:
        line_1 = min(list_line_1, key=itemgetter(3))

    with open(page_2, 'rb') as f:
        file_contents = f.read().decode('utf-8')
        shematics_2 = file_contents.split('\n')

    list_line_2 = []
    for index, line in enumerate(shematics_2):
        if line.startswith('Text '):
            line_fields = line.split()
            if line_fields[1] == 'Label' or line_fields[1] == 'GLabel' or line_fields[1] == 'HLabel':
                line_index_2 = index
                next_line_2 = shematics_2[line_index_2 + 1]
                # if label is precisely at pin location
                if line_fields[2] == pin_2_loc[0] and line_fields[3] == pin_2_loc[1]:
                    list_line_2.append((line, next_line_2, line_index_2, 0.0))
                    logger.info("Found label at pin 2")
                # or if label text matches the net name and is close enoght
                if next_line_2.rstrip() == net_name_2:
                    label_location = (line_fields[2], line_fields[3])
                    distance = get_distance(pin_2_loc, label_location)
                    list_line_2.append((line, next_line_2, line_index_2, distance))
                    logger.info("Found label near pin 2")

    # remove duplicates
    list_line_2 = list(set(list_line_2))
    logger.info("list_line_2="+repr(list_line_2))
    # find closest label
    if len(list_line_2) == 0:
        line_2 = None
    if len(list_line_2) == 1:
        line_2 = list_line_2[0]
    if len(list_line_2) > 1:
        line_2 = min(list_line_2, key=itemgetter(3))

    # swap the labels
    if line_1 is None and line_2 is None:
        logger.info("Could not find the pins connection. \nEither the pins are disconnected or they are connected through short wire segment\nand net name was overriden by some other label.")
        raise ValueError("It makes no sense in swapping two disconneted pins!")
    # if both pins are connected, just swap them
    # if pins are on the same page
    if page_1 == page_2:
        logger.info("Swapping on the same page")
        if line_1 is not None and line_2 is not None:
            logger.info("Both pins are connected")
            new_shematics = list(shematics_1)
            new_shematics[line_1[2]+1] = line_2[1]
            new_shematics[line_2[2]+1] = line_1[1]
        # otherwise you have to move the pin to new location
        elif line_1 is None:
            logger.info("Only pin 2 is connected")
            new_shematics = list(shematics_1)
            line_fields = line_2[0].split()
            line_fields[4] = pin_1_rot
            line_fields[2] = pin_1_loc[0]
            line_fields[3] = pin_1_loc[1]
            new_shematics[line_2[2]] = " ".join(line_fields) + "\n"
        elif line_2 is None:
            logger.info("Only pin 1 is connected")
            new_shematics = list(shematics_1)
            line_fields = line_1[0].split()
            line_fields[4] = pin_2_rot
            line_fields[2] = pin_2_loc[0]
            line_fields[3] = pin_2_loc[1]
            new_shematics[line_1[2]] = " ".join(line_fields) + "\n"

        logger.info("Labels swapped")

        # save schematics
        if __name__ == "__main__":
            sch_file_to_write = os.path.join(os.path.dirname(page_1),
                                             'temp_' + os.path.basename(page_1))
        else:
            sch_file_to_write = page_1
        with open(sch_file_to_write, 'wb') as f:
            f.write("\n".join(new_shematics).encode('utf-8'))
        logger.info("Saved the schematics in same file.")

    # pins are on different pages
    else:
        logger.info("Swapping on the different pages")
        # easy case, label are on both pages, just swap names
        if line_1 is not None and line_2 is not None:
            logger.info("Both pins are connected")
            new_shematics_1 = list(shematics_1)
            new_shematics_2 = list(shematics_2)
            new_shematics_1[line_1[2]+1] = line_2[1]
            new_shematics_2[line_2[2]+1] = line_1[1]
        # hard cases, cut label from one page, and paste it at the end of the other page
        elif line_1 is None:
            logger.info("Only pin 2 is connected")
            new_shematics_2 = list(shematics_2[:line_2[2]] + shematics_2[line_2[2]+2:])
            line_fields = shematics_2[line_2[2]].split()
            line_fields[4] = pin_1_rot
            line_fields[2] = pin_1_loc[0]
            line_fields[3] = pin_1_loc[1]
            new_lines = [" ".join(line_fields) + "\n", shematics_2[line_2[2]+1]]
            new_shematics_1 = list(shematics_1[:-1] + new_lines + shematics_1[-1:])
        elif line_2 is None:
            logger.info("Only pin 1 is connected")
            new_shematics_1 = list(shematics_1[:line_1[2]] + shematics_1[line_1[2]+2:])
            line_fields = shematics_1[line_1[2]].split()
            line_fields[4] = pin_2_rot
            line_fields[2] = pin_2_loc[0]
            line_fields[3] = pin_2_loc[1]
            new_lines = [" ".join(line_fields) + "\n", shematics_1[line_1[2]+1]]
            new_shematics_2 = list(shematics_2[:-1] + new_lines + shematics_2[-1:])

        logger.info("Labels swapped")

        # save schematics
        if __name__ == "__main__":
            filename1 = os.path.basename(page_1).replace(".sch", "_temp.sch")
            sch_file_to_write_1 = os.path.join(os.path.dirname(page_1), filename1)
            filename2 = os.path.basename(page_2).replace(".sch", "_temp.sch")
            sch_file_to_write_2 = os.path.join(os.path.dirname(page_2), filename2)
        else:
            sch_file_to_write_1 = page_1
            sch_file_to_write_2 = page_2
        with open(sch_file_to_write_1, 'wb') as f:
            f.write("\n".join(new_shematics_1).encode('utf-8'))
        with open(sch_file_to_write_2, 'wb') as f:
            f.write("\n".join(new_shematics_2).encode('utf-8'))
        logger.info("Saved the schematics in different files.")

    # swap nets in layout
    # Select PADa -> Properties.Copy NetName
    net_1 = pad_1.GetNet()
    net_2 = pad_2.GetNet()
    pad_2.SetNet(net_1)
    pad_1.SetNet(net_2)
    logger.info("Pad nets swapped")

    # save board
    if __name__ == "__main__":
        pcb_file_to_write = board.GetFileName().replace(".kicad_pcb", "_temp.kicad_pcb")
        pcbnew.SaveBoard(pcb_file_to_write, board)
    logger.info("Saved the layout.")


def get_distance(point1, point2):
    return math.hypot(int(point1[0])-int(point2[0]), int(point1[1])-int(point2[1]))


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
        for line in sheet_reference:
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
        yield subsheet_path, subsheet_line


def find_all_sch_files(filename, list_of_files):
    list_of_files.append(filename)
    for sheet, line_nr in extract_subsheets(filename):
        logger.info("found subsheet:\n\t" + sheet +
                    "\n in:\n\t" + filename + ", line: " + str(line_nr))
        seznam = find_all_sch_files(sheet, list_of_files)
        list_of_files = seznam
    return list_of_files


def main():
    """ test_list = ('local', 'local_partial', 'global', 'global_partial_vertical',
                 'hierarchical', 'across_hierarchy', 'across_hierarchy_wire', 'across_hierarchy_partial_wire',
                 'label_orientation_both', 'label_orientation_single', 'across_multiple_hierarchy')"""
    test_list = ('across_multiple_hierarchy', )
    # local - swap two local labels
    # local_partial - swap one local label
    # global - swap two global labels
    # global_partial_vertical - swap one global label vertical
    # hierarchical - swap two hirarchial labels
    # across_hierarchy - swap to label accross different hiarchical levels
    # across_hierarchy_wire - swap two labels connected thorugh wire across hirarchical levels
    # across_hierarchy_partial_wire - swap one label connected thorugh wire across hierarchical levels
    # label_orientation_both ??
    # label_orientation_single ??
    # across_multiple_hierarchy - test pinswap across multiple hierarchy
    for test in test_list:

        if test == 'local':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U201')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'21':
                    pad1 = pad
                if pad.GetPadName() == u'22':
                    pad2 = pad
            logger.info("Testing local")
            swap(board, pad1, pad2)
        if test == 'local_partial':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U201')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'27':
                    pad1 = pad
                if pad.GetPadName() == u'28':
                    pad2 = pad
            logger.info("Testing local_partial")
            swap(board, pad1, pad2)
        if test == 'global_partial_vertical':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U101')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'37':
                    pad1 = pad
                if pad.GetPadName() == u'12':
                    pad2 = pad
            logger.info("Testing global_partial_vertical")
            swap(board, pad1, pad2)
        if test == 'hierarchical':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U301')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'17':
                    pad1 = pad
                if pad.GetPadName() == u'18':
                    pad2 = pad
            logger.info("Testing hierarchical")
            swap(board, pad1, pad2)
        if test == 'global':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U101')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'35':
                    pad1 = pad
                if pad.GetPadName() == u'36':
                    pad2 = pad
            logger.info("Testing global")
            swap(board, pad1, pad2)
        if test == 'across_hierarchy':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U1')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'1':
                    pad1 = pad
                if pad.GetPadName() == u'8':
                    pad2 = pad
            logger.info("Testing across_hierarchy")
            swap(board, pad1, pad2)
        if test == 'across_hierarchy_wire':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U1')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'10':
                    pad1 = pad
                if pad.GetPadName() == u'3':
                    pad2 = pad
            logger.info("Testing across_hierarchy_wire")
            swap(board, pad1, pad2)
        if test == 'across_hierarchy_partial_wire':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U1')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'2':
                    pad1 = pad
                if pad.GetPadName() == u'9':
                    pad2 = pad
            logger.info("Testing across_hierarchy_partial_wire")
            swap(board, pad1, pad2)
        if test == 'label_orientation_both':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U101')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'13':
                    pad1 = pad
                if pad.GetPadName() == u'15':
                    pad2 = pad
            logger.info("Testing label_orientation_both")
            swap(board, pad1, pad2)
        if test == 'label_orientation_single':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U101')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'13':
                    pad1 = pad
                if pad.GetPadName() == u'16':
                    pad2 = pad
            logger.info("Testing label_orientation_single")
            swap(board, pad1, pad2)
        if test == 'across_multiple_hierarchy':
            board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
            mod = board.FindModuleByReference('U3')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'10':
                    pad1 = pad
                if pad.GetPadName() == u'3':
                    pad2 = pad
            logger.info("Testing across_multiple_hierarhy")
            swap(board, pad1, pad2)


# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt='%(asctime)s %(name)s %(lineno)d:%(message)s',
                                  datefmt='%m-%d %H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    fh = logging.FileHandler("swap_pins.log", "w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("Swap pins plugin version: " + VERSION + " started in standalone mode")

    main()
