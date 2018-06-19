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


class SwapUnitsDialog(wx.Dialog):

    def __init__(self, parent):

        

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

        # load board
        board = pcbnew.GetBoard()
                    
        # check if there are precisely two pads selected
        
        
        # get respective nets
        
        
        # open the schematics, find the pins and nearbywires connecte to the respective nets
        
        
        # swap netnames in schematics
        
        
        # save schematics
        
        
        # swap nets in layout
        
        
        # save layout
        
        

