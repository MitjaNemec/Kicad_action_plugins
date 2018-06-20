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



class SwapUnits(pcbnew.ActionPlugin):
    """
    A script to swap selected pins
    How to use:
    - move to GAL
    - select pads with same function on two different units within same footprint to swap
    - call the plugin
    """

    def defaults(self):
        self.name = "Swap units"
        self.category = "Modify Drawing PCB and schematics"
        self.description = "Swap selected units"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        caption = 'Swap units'
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
        swap_units.swap(board, pad1, pad2)
        
        

