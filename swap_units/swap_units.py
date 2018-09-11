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
import re
import logging
import sys

logger = logging.getLogger(__name__)


def swap(board, pad_1, pad_2):
    logger.info("Starting swap_units")

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

    # get module reference
    footprint_reference = pad_2.GetParent().GetReference()

    logger.info("Swaping units on: " + footprint_reference)

    # get all schematic pages
    all_sch_files = []
    all_sch_files = find_all_sch_files(sch_file, all_sch_files)
    all_sch_files = list(set(all_sch_files))

    # find all schematic pages containing reference
    relevant_sch_files = []
    for page in all_sch_files:
        with open(page) as f:
            current_sch_file = f.read()
        if footprint_reference in current_sch_file:
            relevant_sch_files.append(page)

    logger.info("Sch files to modify are: " + relevant_sch_files[0])

    # link refernce to symbol
    with open(relevant_sch_files[0]) as f:
        # go through all components
        contents = f.read()
        components = contents.split('$Comp')
        for component in components:
            if footprint_reference in component:
                symbol_name = component.split()[1]
                break

    logger.info("Symbol name is: " + symbol_name)

    # load the symbol from cache library
    with open(cache_file) as f:
        contents = f.read()
        symbols = contents.split('ENDDEF')
        for sym in symbols:
            if symbol_name in sym:
                break
    # cleanup everything before DEF
    symbol = sym.split('DEF')[1]

    # grab the pins
    symbol_pins = []
    symbol_fields = symbol.split('\n')
    for field in symbol_fields:
        if field.startswith('X '):
            symbol_pins.append(tuple(field.split()))

    # get number of units
    unit_nr = int(max(symbol_pins, key=lambda item: item[9])[9])

    logger.info("Number of units in symbols: " + str(unit_nr))

    # construct a list of units, where each unit contains its pins. pin order is the same for all units
    sorted_by_pin_name = sorted(symbol_pins, key=lambda tup: (tup[1], tup[9]))
    pins_by_unit = []
    for i in range(unit_nr):
        pins_by_unit.append([])

    for pin in sorted_by_pin_name:
        pins_by_unit[int(pin[9])-1].append(pin)

    # find which units the pads are connected to
    for pin in symbol_pins:
        if pin[2] == pad_nr_1:
            unit_1 = pin[9]
            break
    for pin in symbol_pins:
        if pin[2] == pad_nr_2:
            unit_2 = pin[9]
            break

    logger.info("Units to swap are: " + unit_1 + ", " + unit_2)

    # find pages containing specific units
    page_1 = None
    page_2 = None
    for page in relevant_sch_files:
        with open(page) as f:
            current_sch_file = f.read()
            if footprint_reference in current_sch_file:
                components = current_sch_file.split('$Comp')
                for component in components:
                    if footprint_reference in component:
                        for fields in filter(None, component.split('\n')):
                            if fields[0] == 'U':
                                if fields.split()[1] == unit_1:
                                    page_1 = page
                                if fields.split()[1] == unit_2:
                                    page_2 = page
    logger.info("Files where the unites are:\n\t"
                + page_1 or "None" + "\n\t"
                + page_2 or "None")

    # swap units in schematics
    if page_1 is not None:
        with open(page_1) as f:
            current_sch_file = f.read()
            # find location of specific unit
            comp_starts = [m.start() for m in re.finditer('\$Comp', current_sch_file)]
            comp_ends = [m.start() for m in re.finditer('\$EndComp', current_sch_file)]
            for comp in zip(comp_starts, comp_ends):
                data = current_sch_file[comp[0]:comp[1]].split('\n')
                if footprint_reference in data[1]:
                    if unit_1 in data[2].split()[1]:
                        # +2 +1 account for splits
                        unit_1_loc = data[2].split()[1].find(unit_1)\
                                   + comp[0]\
                                   + len(data[0])\
                                   + len(data[1])\
                                   + len(data[2].split()[0])\
                                   + 2 + 1
                        break
            # swap the unit
            unit_1_sch_file = current_sch_file[:unit_1_loc] + unit_2 + current_sch_file[unit_1_loc + len(unit_1):]

    if page_2 is not None:
        with open(page_2) as f:
            current_sch_file = f.read()
            # find location of specific unit
            comp_starts = [m.start() for m in re.finditer('\$Comp', current_sch_file)]
            comp_ends = [m.start() for m in re.finditer('\$EndComp', current_sch_file)]
            for comp in zip(comp_starts, comp_ends):
                data = current_sch_file[comp[0]:comp[1]].split('\n')
                if footprint_reference in data[1]:
                    if unit_2 in data[2].split()[1]:
                        # +2 +1 account for splits
                        unit_2_loc = data[2].split()[1].find(unit_2)\
                                   + comp[0]\
                                   + len(data[0])\
                                   + len(data[1])\
                                   + len(data[2].split()[0])\
                                   + 2 + 1
                        break
            # swap the unit
            unit_2_sch_file = current_sch_file[:unit_2_loc] + unit_1 + current_sch_file[unit_2_loc + len(unit_2):]

    # if files are the same, then merge two strings
    if page_1 == page_2:
        # reswap in cascade swap the unit
        unit_1_sch_file = current_sch_file[:unit_1_loc] + unit_2 + current_sch_file[unit_1_loc + len(unit_1):]
        unit_2_sch_file = unit_1_sch_file[:unit_2_loc] + unit_1 + unit_1_sch_file[unit_2_loc+len(unit_2):]
        if __name__ == "__main__":
            with open(page_2+'_alt', 'w') as f:
                f.write(unit_2_sch_file)
        else:
            with open(page_2, 'w') as f:
                f.write(unit_2_sch_file)
    # if files are different, then there is no problem, write both of them and be done with it
    else:
        if __name__ == "__main__":
            if page_1 is not None:
                with open(page_1+'_alt', 'w') as f:
                    f.write(unit_1_sch_file)
            if page_2 is not None:
                with open(page_2+'_alt', 'w') as f:
                    f.write(unit_2_sch_file)
        else:
            if page_1 is not None:
                with open(page_1, 'w') as f:
                    f.write(unit_1_sch_file)
            if page_2 is not None:
                with open(page_2, 'w') as f:
                    f.write(unit_2_sch_file)
    logger.info("Saved the schematics.")

    # swap pins in layout
    module = pad_1.GetParent()
    module_pads = module.PadsList()
    pins_of_unit_1 = pins_by_unit[int(unit_1) - 1]
    pins_of_unit_2 = pins_by_unit[int(unit_2) - 1]
    for pins_to_swap in zip(pins_of_unit_1, pins_of_unit_2):
        for pad in module_pads:
            if pad.GetName() == pins_to_swap[0][2]:
                pad_x = pad
            if pad.GetName() == pins_to_swap[1][2]:
                pad_y = pad
        net_x = pad_x.GetNet()
        net_y = pad_y.GetNet()
        pad_x.SetNet(net_y)
        pad_y.SetNet(net_x)

    # save board
    if __name__ == "__main__":
        pcb_file_to_write = 'temp_' + board.GetFileName()
        pcbnew.SaveBoard(pcb_file_to_write, board)
    logger.info("Saved the layout.")


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
    # same_sheet, different_sheets
    test = 'same_sheet'
    if test == 'same_sheet':
        board = pcbnew.LoadBoard('swap_units_test.kicad_pcb')
        mod = board.FindModuleByReference('U1')
        pads = mod.Pads()
        for pad in pads:
            if pad.GetPadName() == u'1':
                pad1 = pad
            if pad.GetPadName() == u'7':
                pad2 = pad
        swap(board, pad1, pad2)
    if test == 'different_sheets':
        board = pcbnew.LoadBoard('swap_units_test.kicad_pcb')
        mod = board.FindModuleByReference('U1')
        pads = mod.Pads()
        for pad in pads:
            if pad.GetPadName() == u'8':
                pad1 = pad
            if pad.GetPadName() == u'14':
                pad2 = pad
        swap(board, pad1, pad2)


# for testing purposes only
if __name__ == "__main__":
    file_handler = logging.FileHandler(filename='swap_units.log', mode='w')
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    # handlers = [file_handler]

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        handlers=handlers
                        )

    logger = logging.getLogger(__name__)
    logger.info("Swap units plugin started in standalone mode")

    main()

