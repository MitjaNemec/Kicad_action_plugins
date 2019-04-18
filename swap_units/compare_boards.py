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


def getIndex(s, i): 
    from collections import deque 
    # If input is invalid. 
    if s[i] != '(': 
        return -1
    # Create a deque to use it as a stack. 
    d = deque() 
    # Traverse through all elements 
    # starting from i. 
    for k in range(i, len(s)): 
        # Pop a starting bracket 
        # for every closing bracket 
        if s[k] == ')': 
            d.popleft() 
        # Push all starting brackets 
        elif s[k] == '(': 
            d.append(s[i]) 
        # If deque becomes empty 
        if not d: 
            return k 
    return -1

def remove_kicad_pcb_header(file_contents):
    """
       remove from file:
        -verision info
        -host info
        -general info
        -page info
        -layers
        -setup info
        -title info
    """
    index_version_start = file_contents.find("(version")
    index_version_stop = getIndex(file_contents, index_version_start)+1
    trimmed_contents = file_contents[0:index_version_start] + file_contents[index_version_stop:-1]

    index_version_start = trimmed_contents.find("(host")
    index_version_stop = getIndex(trimmed_contents, index_version_start)+1
    trimmed_contents = trimmed_contents[0:index_version_start] + trimmed_contents[index_version_stop:-1]

    index_version_start = trimmed_contents.find("(general")
    index_version_stop = getIndex(trimmed_contents, index_version_start)+1
    trimmed_contents = trimmed_contents[0:index_version_start] + trimmed_contents[index_version_stop:-1]

    index_version_start = trimmed_contents.find("(page")
    index_version_stop = getIndex(trimmed_contents, index_version_start)+1
    trimmed_contents = trimmed_contents[0:index_version_start] + trimmed_contents[index_version_stop:-1]

    index_version_start = trimmed_contents.find("(layers")
    index_version_stop = getIndex(trimmed_contents, index_version_start)+1
    trimmed_contents = trimmed_contents[0:index_version_start] + trimmed_contents[index_version_stop:-1]

    index_version_start = trimmed_contents.find("(setup")
    index_version_stop = getIndex(trimmed_contents, index_version_start)+1
    trimmed_contents = trimmed_contents[0:index_version_start] + trimmed_contents[index_version_stop:-1]

    index_version_start = trimmed_contents.find("(title_block")
    index_version_stop = getIndex(trimmed_contents, index_version_start)+1
    trimmed_contents = trimmed_contents[0:index_version_start] + trimmed_contents[index_version_stop:-1]

    return trimmed_contents

def compare_boards(filename1, filename2):
    import difflib
    errnum = 0
    with open(filename1) as f1:
        with open(filename2) as f2:
            contents_f1 = f1.read()
            contents_f2 = f2.read()

    contents_f1 = remove_kicad_pcb_header(contents_f1).split("\n")
    contents_f2 = remove_kicad_pcb_header(contents_f2).split("\n")

    # get a diff
    diff = difflib.unified_diff(
                contents_f1,
                contents_f2,
                fromfile='board1',
                tofile='board2',
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
        index = diffstring.index(line)
        if '@@' in line:
            if (('tstamp' in diffstring[index + 1]) and ('tstamp' in diffstring[index + 2])):
                # this is not a problem
                pass
            else:
                # this is a problem
                errnum = errnum + 1
    return errnum