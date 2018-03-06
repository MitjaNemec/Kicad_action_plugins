#  action_delete_selected.py
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

___version___ = "1.0"


class DeleteLayoutDialog(wx.Dialog):

    def __init__(self, parent):

        self.parent = parent
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Delete selected", pos = wx.DefaultPosition, size = wx.Size( 223,200 ), style = wx.DEFAULT_DIALOG_STYLE )
        
        bSizer1 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
        bSizer3 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_staticText1 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"Delete selected", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )
        bSizer3.Add( self.m_staticText1, 0, wx.ALL, 5 )
        
        self.chkbox_tracks = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Tracks", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.chkbox_tracks.SetValue(True) 
        bSizer3.Add( self.chkbox_tracks, 0, wx.ALL, 5 )
        
        self.chkbox_zones = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Zones", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.chkbox_zones, 0, wx.ALL, 5 )
        
        self.chkbox_modules = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Modules", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.chkbox_modules, 0, wx.ALL, 5 )
        
        
        self.m_panel1.SetSizer( bSizer3 )
        self.m_panel1.Layout()
        bSizer3.Fit( self.m_panel1 )
        bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )
        
        bSizer31 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.btn_ok = wx.Button( self, wx.ID_OK, u"Ok", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer31.Add( self.btn_ok, 0, wx.ALL, 5 )
        
        self.btn_cancel = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer31.Add( self.btn_cancel, 0, wx.ALL, 5 )
        
        
        bSizer1.Add( bSizer31, 1, wx.EXPAND, 5 )
        
        self.SetSizer( bSizer1 )
        self.Layout()
        
        self.Centre( wx.BOTH )

        # bind any numeric key event to function
        randomId = wx.NewId()
        self.Bind(wx.EVT_MENU, self.onKeyPressed, id=randomId)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, ord('1'), randomId)])
        self.SetAcceleratorTable(accel_tbl)

        #self.Bind(wx.EVT_KEY_DOWN, self.onKeyPressed)

    def onKeyPressed(self, event):
        pcbnew.LSET.RemoveLayer(pcbnew.F_Cu)
        # pcbnew.GetBoard().SetVisibleLayers(layer_mask)

        event.Skip()

class DeleteSelected(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - select modules/tracks/zones to delete
    - call the plugin
    - choose which items to delete
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
                    
        # check if there is anything selected
        all_tracks = board.GetTracks()
        selected_tracks = filter(lambda x: x.IsSelected(), all_tracks)
        
        all_zones = []
        for zoneid in range(board.GetAreaCount()):
            all_zones.append(board.GetArea(zoneid))
        selected_zones = filter(lambda x: x.IsSelected(), all_zones)
        
        all_modules = board.GetModules()
        selected_modules = filter(lambda x: x.IsSelected(), all_modules)

        # if anything is selected
        if len(selected_tracks) > 0 or len(selected_zones) > 0 or len(selected_modules) > 0:
            # show dialog
            dlg = DeleteLayoutDialog(_pcbnew_frame)
            res = dlg.ShowModal()
            
            # if user clicked OK
            if res == wx.ID_OK:
                if dlg.chkbox_tracks.GetValue():
                    for track in selected_tracks:
                        board.RemoveNative(track)
                        
                if dlg.chkbox_zones.GetValue():
                    for zone in selected_zones:
                        board.RemoveNative(zone)
                
                if dlg.chkbox_modules.GetValue():
                    for mod in selected_modules:
                        board.RemoveNative(mod)

        # if more or less than one show only a messagebox
        else:
            caption = 'Delete selected'
            message = "Nothing is selected !"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        pass


