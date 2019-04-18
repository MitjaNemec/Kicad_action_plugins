# -*- coding: utf-8 -*-
#  replicatelayout.py
#
# Copyright (C) 2018 Mitja Nemec, Stephen Walker-Weinshenker
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
import os
import re
import logging

logger = logging.getLogger(__name__)


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

    def __init__(self, filename):
        main_sch_file = filename
        self.project_folder = os.path.dirname(main_sch_file)
        # get relation between sheetname and it's id
        logger.info('getting project hierarchy from schematics')
        self.dict_of_sheets = self.find_all_sch_files(main_sch_file, {})
        logger.info("Project hierarchy looks like:\n%s" % repr(self.dict_of_sheets))


def compare_schematics(filename1, filename2):
    # first get list of all sch file in a project
    sch1_data = SchData(filename1)
    sch2_data = SchData(filename2)
    sch1_list = [x[1] for x in sch1_data.dict_of_sheets.values()]
    sch1_list.append(filename1)
    sch2_list = [x[1] for x in sch2_data.dict_of_sheets.values()]
    sch2_list.append(filename2)
    sch1_list = sorted(list(set(sch1_list)))
    sch2_list = sorted(list(set(sch2_list)))

    # if listst are not equeal in length, stop immediatela
    if len(sch1_list) != len(sch2_list):
        return -1

    # do a diff on each file
    err = 0
    for item in zip(sch1_list, sch2_list):
        err = err + compare_sch_files(item[0], item[1])

    return err


def compare_sch_files(filename1, filename2):
    import difflib
    errnum = 0
    with open(filename1) as f1:
        with open(filename2) as f2:
            contents_f1 = f1.read()
            contents_f2 = f2.read()

    # get a diff
    diff = difflib.unified_diff(
                contents_f1,
                contents_f2,
                fromfile='sch1',
                tofile='sch2',
                n=0)

    # only timestamps on zones and file version information should differ
    diffstring = []
    for line in diff:
        diffstring.append(line)
    # if files are the same, finish now
    if not diffstring:
        return 0
    # get rid of diff information
    del diffstring[0]
    del diffstring[0]
    # walktrough diff list and check for any significant differences
    for line in diffstring:
        errnum = errnum + 1
    return errnum
