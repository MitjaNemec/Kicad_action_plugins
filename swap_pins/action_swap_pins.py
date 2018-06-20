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

import wx
import pcbnew
import os
import swap_pins

class SwapPins(pcbnew.ActionPlugin):
    """
    A script to swap selected pins
    How to use:
    - move to GAL
    - select two pads to swap
    - call the plugin
    """

    def defaults(self):
        self.name = "Swap pins"
        self.category = "Modify Drawing PCB and schematics"
        self.description = "Swap selected pins"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        caption = 'Swap pins'
        message = "Is eeschema closed?"
        dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res == wx.ID_NO:
            caption = 'Swap pins'
            message = "You need to close eeschema and then run the plugin again!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # load board
        board = pcbnew.GetBoard()
                    
        # check if there are precisely two pads selected
        selected_pads = filter(lambda x: x.IsSelected(), pcbnew.GetBoard().GetPads())
        if len(selected_pads) != 2:
            caption = 'Swap pins'
            message = "More or less than 2 pads selected. Please select exactly two pads and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # are they on the same module
        pad1 = selected_pads[0]
        pad2 = selected_pads[1]
        if pad1.GetParent().GetReference() != pad2.GetParent().GetReference():
            caption = 'Swap pins'
            message = "Pads don't belong to the same footprint"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # swap pins
        swap_pins.swap(board, pad1, pad2)


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
        
        

