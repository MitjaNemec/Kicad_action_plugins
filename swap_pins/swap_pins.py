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


def swap(board, pad_1, pad_2):
    footprint = pad_2.GetParent().GetReference()
    # get respective nets
    net_1 = pad_1.GetNet()
    net_2 = pad_2.GetNet()
    net_name_1 = net_1.GetNetname()
    net_name_2 = net_2.GetNetname()

    # Find the sch file that has this symbol
    main_sch_file = os.path.abspath(str(board.GetFileName()).replace(".kicad_pcb", ".sch"))
    all_sch_files = []
    all_sch_files = find_all_sch_files(main_sch_file, all_sch_files)
    all_sch_files = list(set(all_sch_files))
    for sch_file in all_sch_files:
        with open(sch_file) as f:
            current_sch_file = f.read()
        if footprint in current_sch_file:
            sch_file_to_modify = sch_file

    # open the schematics, find symbol, find the pins and nearbywires connected to the respective nets
    with open(sch_file_to_modify) as f:
        sch_file = f.readlines()

    # swap netnames in schematics

    # save schematics

    # swap nets in layout
    # Select PADa -> Properties.Copy NetName
    pad_2.SetNet(net_1)
    pad_1.SetNet(net_2)


def extract_subsheets(filename):
    in_rec_mode = False
    counter = 0
    with open(filename) as f:
        file_folder = os.path.dirname(os.path.abspath(filename))
        file_lines = f.readlines()
    for line in file_lines:
        counter += 1
        if not in_rec_mode:
            if line.startswith('$Sheet'):
                in_rec_mode = True
                subsheet_path = []
        elif line.startswith('$EndSheet'):
            in_rec_mode = False
            yield subsheet_path
        else:
            #extract subsheet path
            if line.startswith('F1'):
                subsheet_path = line.split()[1].rstrip("\"").lstrip("\"")
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
                        subsheet_path = subsheet_path.replace("${", "")\
                                                     .replace("}", "")\
                                                     .replace("env_var", path)

                # if path is still not absolute, then it is relative to project
                if not os.path.isabs(subsheet_path):
                    subsheet_path = os.path.join(file_folder, subsheet_path)

                subsheet_path = os.path.normpath(subsheet_path)
                pass


def find_all_sch_files(filename, list_of_files):
    list_of_files.append(filename)
    for sheet in extract_subsheets(filename):
        seznam = find_all_sch_files(sheet, list_of_files)
        list_of_files = seznam
    return list_of_files


def main():
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


# for testing purposes only
if __name__ == "__main__":
    main()