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
from distutils.dir_util import copy_tree

if __name__ != "__main__":
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


def swap(board, pad_1, pad_2):
    logger.info("Starting swap_units")

    # get all file paths
    pcb_file = os.path.abspath(str(board.GetFileName()))
    sch_file = os.path.abspath(str(board.GetFileName()).replace(".kicad_pcb", ".sch"))
    cache_file = os.path.abspath(str(board.GetFileName()).replace(".kicad_pcb", "-cache.lib"))
    project_folder = os.path.dirname(cache_file)

    logger.info("main sch file is: " + sch_file)
    logger.info("main pcb file is: " + pcb_file)
    logger.info("sch cache file is: " + cache_file)

    # get pad numbers
    pad_nr_1 = pad_1.GetPadName()
    pad_nr_2 = pad_2.GetPadName()
    logger.info("Swapping pins: " + pad_nr_1 + "," + pad_nr_2)

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
        with open(page, 'rb') as f:
            current_sch_file = f.read().decode('utf-8')
        if footprint_reference in current_sch_file:
            relevant_sch_files.append(page)

    logger.info("Sch files to modify are: " + repr(relevant_sch_files))

    # link refernce to symbol
    with open(relevant_sch_files[0], 'rb') as f:
        contents = f.read().decode('utf-8')
        # go through all components
        components = contents.split('$Comp')
        for component in components:
            # TODO matching with in is not precise enough (e.g. C401 is in IC401 also)
            if footprint_reference in component:
                symbol_name = component.split()[1]
                break

    logger.info("Symbol name is: " + symbol_name)

    lib_name = symbol_name.rsplit(":", 1)[0]
    sym_name = symbol_name.rsplit(":", 1)[1]

    # load the symbol from cache library
    with open(cache_file, 'rb') as f:
        contents = f.read().decode('utf-8')
        symbols = contents.split('ENDDEF')
        # go throught all symbols and when you hit the correct one, yield
        for sym in symbols:
            # find line stating with DEF
            sym_lines = sym.split("\n")
            for line in sym_lines:
                if line.startswith('DEF'):
                    if lib_name in line and sym_name in line:
                        logger.info("Found symbol " + symbol_name + " in -cache.lib")
                        break
            else:
                continue
            break
        else:
            sym = None

    if sym is None:
        logger.error("Did not find: " + symbol_name + " in -cache.lib")
        raise LookupError("Symbol is missing from -cache.lib")

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
        with open(page, 'rb') as f:
            current_sch_file = f.read().decode('utf-8')
            if footprint_reference in current_sch_file:
                components = current_sch_file.split('$Comp')
                for component in components:
                    component_lines = component.split('\n')
                    L_line = [x for x in component_lines if x.startswith("L ")]
                    U_line = [x for x in component_lines if x.startswith("U ")]
                    AR_lines = [x for x in component_lines if x.startswith("AR ")]
                    if not AR_lines and L_line:
                        if L_line[0].split()[2] == footprint_reference:
                            if U_line[0].split()[1] == unit_1:
                                page_1 = page
                            if U_line[0].split()[1] == unit_2:
                                page_2 = page
                    if AR_lines:
                        check = filter(lambda x: x.split()[2].split("\"")[1] == footprint_reference, AR_lines)
                        if check:
                            if U_line[0].split()[1] == unit_1:
                                page_1 = page
                            if U_line[0].split()[1] == unit_2:
                                page_2 = page

    logger.info("Files where the units are:\n\t"
                + (page_1 or "None") + "\n\t"
                + (page_2 or "None"))

    # swap units in schematics
    if page_1 is not None:
        with open(page_1, 'rb') as f:
            current_sch_file = f.read().decode('utf-8')
            unit_1_loc = None
            unit_1ar_loc = []
            current_sch_file_by_lines = current_sch_file.split("\n")
            # find location of specific unit
            comp_starts = [m.start() for m in re.finditer('\$Comp', current_sch_file)]
            comp_ends = [m.start() for m in re.finditer('\$EndComp', current_sch_file)]
            for comp in zip(comp_starts, comp_ends):
                data = current_sch_file[comp[0]:comp[1]].split('\n')
                # filter lines so that
                L_line = [x for x in data if x.startswith("L ")][0]
                AR_lines = [x for x in data if x.startswith("AR ")]
                # if there is no multiple hierarchy, get the unit location
                # it is easy to check for reference
                if not AR_lines:
                    if L_line.split()[2] == footprint_reference:
                        if unit_1 in data[2].split()[1]:
                            logger.info("Unit 1 is not on multiple hierarchy sheet")
                            logger.info("\n".join(data))
                            logger.info("Unit 1 description is around lines: " + str(current_sch_file[:current_sch_file.find("\n".join(data))].count("\n")+1))
                            # +2 +1 account for splits
                            unit_1_loc = data[2].split()[1].find(unit_1)\
                                       + comp[0]\
                                       + len(data[0])\
                                       + len(data[1])\
                                       + len(data[2].split()[0])\
                                       + 2 + 1
                            break
                # if there is multiple hierarchy, test is somewhat more complex
                else:
                    check = filter(lambda x: x.split()[2].split("\"")[1] == footprint_reference, AR_lines)
                    # check all the AR lines for presence of footprint reference
                    checks = [True for x in AR_lines if x.split()[2].split("\"")[1] == footprint_reference]
                    if any(checks):
                        if unit_1 in data[2].split()[1]:
                            logger.info("Unit 1 is on multiple hierarchy sheet")
                            logger.info("\n".join(data))
                            logger.info("Unit 1 description is around lines: " + str(current_sch_file[:current_sch_file.find("\n".join(data))].count("\n")+1))
                            # replace unit number in  U line
                            # +2 +1 account for splits
                            unit_1_loc = data[2].split()[1].find(unit_1)\
                                       + comp[0]\
                                       + len(data[0])\
                                       + len(data[1])\
                                       + len(data[2].split()[0])\
                                       + 2 + 1
                            # find all AR unit number locations
                            for ar_line in AR_lines:
                                if "Part=\""+unit_1+"\"" in ar_line:
                                    data_index = data.index(ar_line)
                                    unit_1ar_loc.append(  len("\n".join(data[0:data_index]))\
                                                        + len(data[data_index].split("Part=\"")[0])\
                                                        + data[data_index].split("Part=\"")[1].find(unit_1)\
                                                        + comp[0]\
                                                        + 6 + 1)
                            break

            # if unit was not found in the file, something is very wrong
            if unit_1_loc is None:
                raise LookupError("Did not find unit: %s in file %s" % (unit_1, page_1))

            # swap the unit
            logger.info("Swapping unit %s U field" % unit_1)
            unit_1_sch_file = current_sch_file[:unit_1_loc] + unit_2 + current_sch_file[unit_1_loc + len(unit_1):]
            for ar_loc in unit_1ar_loc:
                logger.info("Swapping unit %s AR fields" % unit_1)
                unit_1_sch_file = unit_1_sch_file[:ar_loc] + unit_2 + unit_1_sch_file[ar_loc + len(unit_1):]

    # if page_1 == page_2 do not swap again
    if (page_2 is not None):
        with open(page_2, 'rb') as f:
            current_sch_file = f.read().decode('utf-8')
            unit_2_loc = None
            unit_2ar_loc = []
            current_sch_file_by_lines = current_sch_file.split("\n")
            # find location of specific unit
            comp_starts = [m.start() for m in re.finditer('\$Comp', current_sch_file)]
            comp_ends = [m.start() for m in re.finditer('\$EndComp', current_sch_file)]
            for comp in zip(comp_starts, comp_ends):
                data = current_sch_file[comp[0]:comp[1]].split('\n')
                # filter lines so that
                L_line = [x for x in data if x.startswith("L ")][0]
                AR_lines = [x for x in data if x.startswith("AR ")]
                # if there is no multiple hierarchy, get the unit location
                # it is easy to check for reference
                if not AR_lines:
                    if L_line.split()[2] == footprint_reference:
                        if unit_2 in data[2].split()[1]:
                            logger.info("Unit 2 is not on multiple hierarchy sheet")
                            logger.info("\n".join(data))
                            logger.info("Unit 2 description is around lines: " + str(current_sch_file[:current_sch_file.find("\n".join(data))].count("\n")+1))
                            # +2 +1 account for splits
                            unit_2_loc = data[2].split()[1].find(unit_2)\
                                       + comp[0]\
                                       + len(data[0])\
                                       + len(data[1])\
                                       + len(data[2].split()[0])\
                                       + 2 + 1
                            break
                # if there is multiple hierarchy, test is somewhat more complex
                else:
                    check = filter(lambda x: x.split()[2].split("\"")[1] == footprint_reference, AR_lines)
                    # check all the AR lines for presence of footprint reference
                    checks = [True for x in AR_lines if x.split()[2].split("\"")[1] == footprint_reference]
                    if checks:
                        if unit_2 in data[2].split()[1]:
                            logger.info("Unit 2 is on multiple hierarchy sheet")
                            logger.info("\n".join(data))
                            logger.info("Unit 2 description is around lines: " + str(current_sch_file[:current_sch_file.find("\n".join(data))].count("\n")+1))
                            # +2 +1 account for splits
                            unit_2_loc = data[2].split()[1].find(unit_2)\
                                       + comp[0]\
                                       + len(data[0])\
                                       + len(data[1])\
                                       + len(data[2].split()[0])\
                                       + 2 + 1
                            # find all AR unit number locations
                            for ar_line in AR_lines:
                                if "Part=\""+unit_2+"\"" in ar_line:
                                    data_index = data.index(ar_line)
                                    unit_2ar_loc.append(  len("\n".join(data[0:data_index]))\
                                                        + len(data[data_index].split("Part=\"")[0])\
                                                        + data[data_index].split("Part=\"")[1].find(unit_2)\
                                                        + comp[0]\
                                                        + 6 + 1)
                            break

            # if unit was not found in the file, something is very wrong
            if unit_2_loc is None:
                raise LookupError("Did not find unit: %s in file %s" % (unit_2, page_2))

            # swap the unit
            if page_2 == page_1:
                logger.info("Swapping second unit on the same page")
                logger.info("Swapping unit %s U field" % unit_2)
                unit_2_sch_file = unit_1_sch_file[:unit_2_loc] + unit_1 + unit_1_sch_file[unit_2_loc + len(unit_2):]
                # data = current_sch_file[comp[0]:comp[1]].split('\n')
                for ar_loc in unit_2ar_loc:
                    logger.info("Swapping unit %s AR fields" % unit_2)
                    unit_2_sch_file = unit_2_sch_file[:ar_loc] + unit_1 + unit_2_sch_file[ar_loc + len(unit_2):]
            else:
                logger.info("Swapping second unit on different page")
                logger.info("Swapping unit %s U field" % unit_2)
                unit_2_sch_file = current_sch_file[:unit_2_loc] + unit_1 + current_sch_file[unit_2_loc + len(unit_2):]
                # data = current_sch_file[comp[0]:comp[1]].split('\n')
                for ar_loc in unit_2ar_loc:
                    logger.info("Swapping unit %s AR fields" % unit_2)
                    unit_2_sch_file = unit_2_sch_file[:ar_loc] + unit_1 + unit_2_sch_file[ar_loc + len(unit_2):]

    # before saving the schematics, swap the pins in layout
    # swap pins in layout
    # TODO might want to add also swapping pins in coresponding units in case of multiple schematics
    logger.info("Swapping pins in layout")
    module = pad_1.GetParent()
    module_pads = module.Pads()
    pins_of_unit_1 = pins_by_unit[int(unit_1) - 1]
    pins_of_unit_2 = pins_by_unit[int(unit_2) - 1]
    # generate pretier list of pins, where all the pin data is joined together and serves as a hash for comparison
    pins_of_unit_1_nice = sorted([x[:3] + ("".join(x[3:9]) + "".join(x[10:]), ) for x in pins_of_unit_1], key=lambda x: x[3])
    pins_of_unit_2_nice = sorted([x[:3] + ("".join(x[3:9]) + "".join(x[10:]), ) for x in pins_of_unit_2], key=lambda x: x[3])
    # check if both units have the same number of pins
    if len(pins_of_unit_1_nice) != len(pins_of_unit_2_nice):
        raise LookupError("Units to swap have a different pin count")
    # test if both units have the same pins (all pin data should match)
    for index in range(len(pins_of_unit_1_nice)):
        if pins_of_unit_1_nice[index][3] != pins_of_unit_2_nice[index][3]:
            raise LookupError("Pins in units to swap don't match")

    all_pins_pairs_to_swap_zip = zip(pins_of_unit_1_nice, pins_of_unit_2_nice)
    for pair_to_swap in all_pins_pairs_to_swap_zip:
        for pad in module_pads:
            if pad.GetName() == pair_to_swap[0][2]:
                pad_x = pad
            if pad.GetName() == pair_to_swap[1][2]:
                pad_y = pad
        net_x = pad_x.GetNet()
        net_y = pad_y.GetNet()
        pad_x.SetNet(net_y)
        pad_y.SetNet(net_x)

    # save board
    if __name__ == "__main__":
        dirname = os.path.dirname(os.path.abspath(board.GetFileName()))
        filename = os.path.basename(board.GetFileName())
        new_name = os.path.join(dirname + "_temp", filename)
        pcbnew.SaveBoard(new_name, board)
    logger.info("Saved the layout.")

    # save the schematics
    logger.info("Save the schematics")
    # if files are the same, then merge two strings
    if page_1 == page_2:
        if __name__ == "__main__":
            filename = os.path.basename(page_1)
            subfolder = os.path.relpath(os.path.dirname(page_1))
            new_name = os.path.join(os.path.join(project_folder + "_temp", subfolder), filename)
            with open(new_name, 'wb') as f:
                f.write(unit_2_sch_file.encode('utf-8'))
        else:
            with open(page_1, 'wb') as f:
                f.write(unit_2_sch_file.encode('utf-8'))
    # if files are different, then there is no problem, write both of them and be done with it
    else:
        if __name__ == "__main__":
            filename = os.path.basename(page_1)
            subfolder = os.path.relpath(os.path.dirname(page_1))
            new_name = os.path.join(os.path.join(project_folder + "_temp", subfolder), filename)
            if page_1 is not None:
                with open(new_name, 'wb') as f:
                    f.write(unit_1_sch_file.encode('utf-8'))
            if page_2 is not None:
                filename = os.path.basename(page_2)
                subfolder = os.path.relpath(os.path.dirname(page_2))
                new_name = os.path.join(os.path.join(project_folder + "_temp", subfolder), filename)
                with open(new_name, 'wb') as f:
                    f.write(unit_2_sch_file.encode('utf-8'))
        else:
            if page_1 is not None:
                with open(page_1, 'wb') as f:
                    f.write(unit_1_sch_file.encode('utf-8'))
            if page_2 is not None:
                with open(page_2, 'wb') as f:
                    f.write(unit_2_sch_file.encode('utf-8'))
    logger.info("Saved the schematics.")


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
        #logger.info("found subsheet:\n\t" + sheet +
        #            "\n in:\n\t" + filename + ", line: " + str(line_nr))
        seznam = find_all_sch_files(sheet, list_of_files)
        list_of_files = seznam
    return list_of_files


def main():
    import compare_projects
    os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "swap_units_test_project"))
    test_list = ['same_sheet',
                 'different_sheets',
                 'different_sheets_different_hierarchy',
                 'same_sheet_different_hierarchy',
                 'test_issue']
    test_list = ['test_issue']
    # same_sheet, different_sheets, test_issue
    for test in test_list:
        if test == 'same_sheet':
            # copy fresh project to _temp folder to overwrite previous changes
            copy_tree(os.getcwd(), os.getcwd() + "_temp")
            # load board and find reference module and select proper pads
            board = pcbnew.LoadBoard('swap_units_test.kicad_pcb')
            mod = board.FindModuleByReference('U1')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'1':
                    pad1 = pad
                if pad.GetPadName() == u'7':
                    pad2 = pad
            swap(board, pad1, pad2)
            # compare schematics
            err = compare_projects.compare_projects(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_same_sheet\\swap_units_test.pro'),
                                                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_temp\\swap_units_test.pro'))
            assert (err == 0), "same_sheet failed"
        if test == 'different_sheets':
            # copy fresh project to _temp folder to overwrite previous changes
            copy_tree(os.getcwd(), os.getcwd() + "_temp")
            # load board and find reference module and select proper pads
            board = pcbnew.LoadBoard('swap_units_test.kicad_pcb')
            mod = board.FindModuleByReference('U1')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'8':
                    pad1 = pad
                if pad.GetPadName() == u'14':
                    pad2 = pad
            swap(board, pad1, pad2)
            # compare schematics
            err = compare_projects.compare_projects(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_different_sheets\\swap_units_test.pro'),
                                                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_temp\\swap_units_test.pro'))
            assert (err == 0), "different_sheets failed"
        if test == 'different_sheets_different_hierarchy':
            # copy fresh project to _temp folder to overwrite previous changes
            copy_tree(os.getcwd(), os.getcwd() + "_temp")
            # load board and find reference module and select proper pads
            board = pcbnew.LoadBoard('swap_units_test.kicad_pcb')
            mod = board.FindModuleByReference('U3')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'1':
                    pad1 = pad
                if pad.GetPadName() == u'14':
                    pad2 = pad
            swap(board, pad1, pad2)
            # compare schematics
            err = compare_projects.compare_projects(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_different_sheets_different_hierarchy\\swap_units_test.pro'),
                                                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_temp\\swap_units_test.pro'))
            assert (err == 0), "different_sheets failed"
        if test == 'same_sheet_different_hierarchy':
            # copy fresh project to _temp folder to overwrite previous changes
            copy_tree(os.getcwd(), os.getcwd() + "_temp")
            # load board and find reference module and select proper pads
            board = pcbnew.LoadBoard('swap_units_test.kicad_pcb')
            mod = board.FindModuleByReference('U7')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'7':
                    pad1 = pad
                if pad.GetPadName() == u'14':
                    pad2 = pad
            swap(board, pad1, pad2)
            # compare schematics
            err = compare_projects.compare_projects(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_same_sheet_different_hierarchy\\swap_units_test.pro'),
                                                    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_temp\\swap_units_test.pro'))
            assert (err == 0), "same_sheet_different_hierarchy failed"
        if test == 'test_issue':
            os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_issue"))
            # copy fresh project to _temp folder to overwrite previous changes
            copy_tree(os.getcwd(), os.getcwd() + "_temp")
            # load board and find reference module and select proper pads
            board = pcbnew.LoadBoard('test.kicad_pcb')
            mod = board.FindModuleByReference('IC201')
            pads = mod.Pads()
            for pad in pads:
                if pad.GetPadName() == u'1':
                    pad1 = pad
                if pad.GetPadName() == u'7':
                    pad2 = pad
            swap(board, pad1, pad2)
            # compare schematics
            #err = compare_projects.compare_projects(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_same_sheet_different_hierarchy\\swap_units_test.pro'),
            #                                        os.path.join(os.path.dirname(os.path.realpath(__file__)), 'swap_units_test_project_temp\\swap_units_test.pro'))

# for testing purposes only
if __name__ == "__main__":
    # if debugging outside of this folder change the folder
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    # create standalone logger which will log to file and stdout stream
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logFormatter = logging.Formatter("%(asctime)s %(name)s %(lineno)d:%(message)s'", datefmt='%m-%d %H:%M:%S')

    fileHandler = logging.FileHandler(filename="swap_units.log", mode='w')
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    logger.info("Plugin executed on: " + repr(sys.platform))
    logger.info("Plugin executed with python version: " + repr(sys.version))
    logger.info("KiCad build version: " + BUILD_VERSION)
    logger.info("Swap units plugin version: " + VERSION + " started in standalone mode")

    main()
