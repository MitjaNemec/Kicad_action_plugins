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

import pcbnew
import os
import math
from operator import itemgetter
import re
import logging
import sys

logger = logging.getLogger(__name__)


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
                "on: " + footprint_reference + " on nets: " + net_name_1 + ", " + net_name_2)

    # get all schematic pages
    all_sch_files = []
    all_sch_files = find_all_sch_files(sch_file, all_sch_files)
    all_sch_files = list(set(all_sch_files))

    # find symbol location (in which file and where in canvas)
    relevant_sch_files = []
    for page in all_sch_files:
        # link refernce to symbol
        with open(page) as f:
            # go through all components
            contents = f.read()
            comp_indices = [m.start() for m in re.finditer('\$Comp', contents)]
            endcomp_indices = [m.start() for m in re.finditer('\$EndComp', contents)]

            if len(comp_indices) != len(endcomp_indices):
                raise LookupError("Schematic page contains errors")

            component_locations = zip(comp_indices, endcomp_indices)
            for comp_location in component_locations:
                component_reference = contents[comp_location[0]:comp_location[1]].split('\n')
                symbol_name = None
                for line in component_reference:
                    if line.startswith('L '):
                        if footprint_reference == line.split()[2]:
                            symbol_name = line.split()[1]
                        else:
                            break
                if symbol_name is not None:
                    for line in component_reference:
                        if line.startswith('U '):
                            symbol_unit = line.split()[1]
                        if line.startswith('P '):
                            symbol_loc = (line.split()[1], line.split()[2])
                            relevant_sch_files.append((page, symbol_unit, symbol_loc, symbol_name))
                            break

    # if no symbol has been found raise an expcetion
    if relevant_sch_files is None:
        logger.info("No coresponding symbols found in the schematics")
        raise ValueError("No coresponding symbols found in the schematics")

    # load the symbol from cache library
    with open(cache_file) as f:
        contents = f.read()
        def_indices = [m.start() for m in re.finditer('DEF ', contents)]
        enddef_indices = [m.start() for m in re.finditer('ENDDEF', contents)]
        if len(def_indices) != len(enddef_indices):
            logger.info("Cache library contains errors")
            raise LookupError("Cache library contains errors")
        symbol_locations = zip(def_indices, enddef_indices)
        # go through all the symbols in the library
        for sym_location in symbol_locations:
            sym = contents[sym_location[0]:sym_location[1]].split('\n')
            # go throguh all lines in the symbol and find a mathc
            for line in sym:
                if line.startswith('DEF '):
                    if relevant_sch_files[0][3] in line.split()[1]:
                        # found a match, break from both loops
                        symbol = sym
                        logger.info("Found symbol in cache library")
                        break
            else:
                # Continue if the inner loop wasn't broken.
                continue
            # Inner loop was broken, break the outer.
            break

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
    relevant_pins = []
    for pin in symbol_pins:
        if pin[2] == pad_nr_1:
            relevant_pins.append(pin)
        if pin[2] == pad_nr_2:
            relevant_pins.append(pin)

    unit_1 = relevant_pins[0][9]
    unit_2 = relevant_pins[1][9]

    # get the pages of correcsponding unit
    page_1 = filter(lambda x: x[1] == unit_1, relevant_sch_files)[0][0]
    page_1_loc = filter(lambda x: x[1] == unit_1, relevant_sch_files)[0][2]
    page_2 = filter(lambda x: x[1] == unit_2, relevant_sch_files)[0][0]
    page_2_loc = filter(lambda x: x[1] == unit_2, relevant_sch_files)[0][2]

    logger.info("Unit 1 on page: " + page_1 +
                "at: " + str(page_1_loc[0]) + ", " + str(page_1_loc[1]))
    logger.info("Unit 2 on page: " + page_2 +
                "at: " + str(page_2_loc[0]) + ", " + str(page_2_loc[1]))

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
    with open(page_1) as f:
        shematics_1 = f.readlines()
    # parse it and find text labels at pin locations
    list_line_1 = []
    for line in shematics_1:
        if line.startswith('Text '):
            line_fields = line.split()
            if line_fields[1] == 'Label' or line_fields[1] == 'GLabel' or line_fields[1] == 'HLabel':
                line_index_1 = shematics_1.index(line)
                next_line_1 = shematics_1[line_index_1 + 1]
                # if label is precisely at pin location
                if line_fields[2] == pin_1_loc[0] and line_fields[3] == pin_1_loc[1]:
                    list_line_1.append( (line, next_line_1, line_index_1, 0.0) )
                    logger.info("Found label at pin 1")
                # or if label text matches the net name and is close enoght
                if next_line_1.rstrip() == net_name_1:
                    label_location = (line_fields[2], line_fields[3])
                    distance = get_distance(pin_1_loc, label_location)
                    list_line_1.append( (line, next_line_1, line_index_1, distance) )
                    logger.info("Found label near pin 1")

    # remove duplicates
    list_line_1 = list(set(list_line_1))
    # find closest label
    if len(list_line_1) == 0:
        line_1 = None
    if len(list_line_1) == 1:
        line_1 = list_line_1[0]
    if len(list_line_1) > 1:
        line_1 = min(list_line_1, key=itemgetter(3))

    with open(page_2) as f:
        shematics_2 = f.readlines()

    list_line_2 = []
    for line in shematics_2:
        if line.startswith('Text '):
            line_fields = line.split()
            if line_fields[1] == 'Label' or line_fields[1] == 'GLabel' or line_fields[1] == 'HLabel':
                line_index_2 = shematics_2.index(line)
                next_line_2 = shematics_2[line_index_2 + 1]
                # if label is precisely at pin location
                if line_fields[2] == pin_2_loc[0] and line_fields[3] == pin_2_loc[1]:
                    list_line_2 = (line, next_line_2, line_index_2)
                    logger.info("Found label at pin 2")
                # or if label text matches the net name and is close enoght
                if next_line_2.rstrip() == net_name_2:
                    label_location = (line_fields[2], line_fields[3])
                    distance = get_distance(pin_2_loc, label_location)
                    list_line_2.append((line, next_line_2, line_index_2, distance))
                    logger.info("Found label near pin 2")

    # remove duplicates
    list_line_2 = list(set(list_line_2))
    # find closest label
    if len(list_line_2) == 0:
        line_2 = None
    if len(list_line_2) == 1:
        line_2 = list_line_2[0]
    if len(list_line_2) > 1:
        line_2 = min(list_line_2, key=itemgetter(3))

    # swap the labels
    if line_1 is None and line_2 is None:
        logger.info("It makes no sense in swapping two disconneted pins!")
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
        with open(sch_file_to_write, 'w') as f:
            f.writelines(new_shematics)
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
            sch_file_to_write_1 = os.path.join(os.path.dirname(page_1),
                                               'temp_' + os.path.basename(page_1))
            sch_file_to_write_2 = os.path.join(os.path.dirname(page_2),
                                               'temp_' + os.path.basename(page_2))
        else:
            sch_file_to_write_1 = page_1
            sch_file_to_write_2 = page_2
        with open(sch_file_to_write_1, 'w') as f:
            f.writelines(new_shematics_1)
        with open(sch_file_to_write_2, 'w') as f:
            f.writelines(new_shematics_2)
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
        pcb_file_to_write = 'temp_' + board.GetFileName()
        pcbnew.SaveBoard(pcb_file_to_write, board)
    logger.info("Saved the layout.")


def get_distance(point1, point2):
    return math.hypot(int(point1[0])-int(point2[0]), int(point1[1])-int(point2[1]))


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
    # local - swap two local labels
    # local_partial - swap one local label
    # global - swap two global labels
    # global_partial_vertical - swap one global label vertical
    # hierarchical - swap two hirarchial labels
    # across_hierarchy - swap to label accross different hiarchical levels
    # across_hierarchy_wire - swap two labels connected thorugh wire across hirarchical levels
    # across_hierarchy_partial_wire - swap one label connected thorugh wire across hierarchical levels
    test = 'across_hierarchy_partial_wire'

    if test == 'local':
        board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
        mod = board.FindModuleByReference('U201')
        pads = mod.Pads()
        for pad in pads:
            if pad.GetPadName() == u'21':
                pad1 = pad
            if pad.GetPadName() == u'22':
                pad2 = pad
        pass
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
        pass
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
        pass
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
        pass
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
        pass
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
        pass
        swap(board, pad1, pad2)
    if test == 'across_hierarchy_wire':
        board = pcbnew.LoadBoard('swap_pins_test.kicad_pcb')
        mod = board.FindModuleByReference('U1')
        pads = mod.Pads()
        for pad in pads:
            if pad.GetPadName() == u'3':
                pad1 = pad
            if pad.GetPadName() == u'10':
                pad2 = pad
        pass
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
        pass
        swap(board, pad1, pad2)


# for testing purposes only
if __name__ == "__main__":
    file_handler = logging.FileHandler(filename='swap_pins_V2.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    # handlers = [file_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Swap pins plugin started in standalone mode")

    main()