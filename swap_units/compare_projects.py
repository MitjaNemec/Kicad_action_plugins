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

import compare_schematics
import compare_boards

def compare_projects(proj1, proj2):
    sch_file1 = proj1.replace(".pro", ".sch")
    sch_file2 = proj2.replace(".pro", ".sch")
    pcb_file1 = proj1.replace(".pro", ".kicad_pcb")
    pcb_file2 = proj2.replace(".pro", ".kicad_pcb")

    err_sch = compare_schematics.compare_schematics(sch_file1, sch_file2)
    err_pcb = compare_boards.compare_boards(pcb_file1, pcb_file2)

    return err_pcb + err_sch
