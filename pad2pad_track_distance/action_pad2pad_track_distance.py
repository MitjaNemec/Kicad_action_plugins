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
                selected_pads.apped(pad)
                
        # check the nets on all the pads
        nets = []
        for pad in selected_pads:
                nets.append(pad.GetNetname())

        # if two pads are selected
        if len(selected_pads) == 2:
            # and if they are on the same net
            if net[0] == net[1]:
                pass
                # TODO
                # poisci vse track-e
                tracks = board.GetTracks()
                
                # poisci samo track-e ki so na pravem net-u
                tracks_on_net = []
                for track in tracks:
                    track_net_name = track.GetNetname()
                    if track_net_name == net[0]:
                        tracks_on_net.append(track)

                # starting point and layer
                start_point = pad[0].GetPosition()
                start_layer = pad[0].GetLayer()
                
                end_point = pad[1].GetPosition()
                end_layer = pad[1].GetLayer()
                # current point and layer
                                
                lenght = get_new_endpoints(start_point, start_layer, 0, tracks_on_net)
                
                # go through the list and find minimum
                min_length = min(lenght)
                
                caption = 'Pad2Pad Track Distance'
                message = "Distance between pads is " + str(min_length) + " mm" 
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

    def get_new_endpoints(point, layer, length, track_list)
        ret_len = [lenght]
        # find track at this endpoint
        for track in track_list:
            # if via, swap layer
            if track.GetClass() == "VIA":
                new_layer = "Any"
                new_point = point
                # remove current track from list so that we don't iterate over it
                new_track_list = list(track_list).remove(track)
            else:
                point1 = track.GetStart()
                point2 = track.GetEnd()
                track_layer = track.GetLayer()
                # remove current track from list so that we don't iterate over it
                new_track_list = list(track_list).remove(track)
                # if on same layer and start at the same point
                if (track_layer == layer or layer == "Any") and (point1 == point or point2 == point):
                    if point1 == point:
                        new_point = point2
                    if point2 == point:
                        new_point = point1
                    length = length + track.GetLength()/SCALE
                    # check if this is the last track
                    if new_point == end_point and new_layer == end_layer:
                        new_point = None
                        new_layer = None
                # ce pa je to slepa veja
                else:
                    new_point = None
                    new_layer = None
                    ret_len[0] = None
            # ce se nismo na koncu, potem grem napre
            if new_point is not None:
                ret_len.append(get_new_endpoints(new_point, new_layer, length, new_track_list))
        return ret_len

