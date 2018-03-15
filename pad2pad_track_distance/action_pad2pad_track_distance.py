#  action_pad2pad_track_distance.py
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
import pad2pad_track_distance

SCALE = 1000000.0


class Pad2PadTrackDistance(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - select two pads
    - call the plugin
    """

    def defaults(self):
        self.name = "Delete selected"
        self.category = "Modify Drawing PCB"
        self.description = "Delete selected elements"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        # load board
        board = pcbnew.GetBoard()
                    
        # get all pads
        modules = board.GetModules()
        
        pads = []
        for mod in modules:
            # get their pads
            module_pads = mod.PadsList()
            # get net
            for pad in module_pads:
                pads.append(pad)
                
        # get list of all selected pads
        selected_pads = []
        for pad in pads:
            if pad.IsSelected():
                selected_pads.append(pad)

        # check the nets on all the pads
        nets = []
        for pad in selected_pads:
                nets.append(pad.GetNetname())

        # if two pads are selected
        if len(selected_pads) == 2:
            # and if they are on the same net
            if nets[0] == nets[1]:
                measure_distance = pad2pad_track_distance.Distance(board, selected_pads[0], selected_pads[1])
                distance = measure_distance.get_length()

                # deselect pads
                selected_pads[0].ClearSelected()
                selected_pads[1].ClearSelected()
                # select tracks
                for track in measure_distance.track_list[1:-1]:
                    track.SetSelected()

                caption = 'Pad2Pad Track Distance'
                message = "Distance between pads is " + str(distance) + " mm"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()  
                
            else:
                caption = 'Pad2Pad Track Distance'
                message = "The selected pads are not on the same net"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()        
            
        # if more or less than one show only a messagebox
        else:
            caption = 'Pad2Pad Track Distance'
            message = "You have to select two and only two pads"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        pass



