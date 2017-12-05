#  action_replicate_layout.py
#
# Copyright (C) 2017 Mitja Nemec
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
import replicatelayout

___version___ = "1.0"


class ReplicateLayoutDialog(wx.Dialog):
    def __init__(self, parent, radius, width, angle):

        self.minimum_radius = radius
        self.minimum_width = width
        self.minimum_angle = angle

        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Replicate layout", pos=wx.DefaultPosition,
                           size=wx.Size(270, 387), style=wx.DEFAULT_DIALOG_STYLE)

        #self.SetSizeHints(wx.Size(-1, -1), wx.Size(-1, -1))

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        bSizer9 = wx.BoxSizer(wx.VERTICAL)

        coordinate_systemChoices = [u"Cartesian", u"Polar"]
        self.coordinate_system = wx.RadioBox(self, wx.ID_ANY, u"Coordinate system", wx.DefaultPosition,
                                             wx.Size(250, -1), coordinate_systemChoices, 2, wx.RA_SPECIFY_COLS)
        self.coordinate_system.SetSelection(0)
        bSizer9.Add(self.coordinate_system, 0, wx.ALL, 5)

        bSizer1.Add(bSizer9, 1, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_x_mag = wx.StaticText(self, wx.ID_ANY, u"x offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_x_mag.Wrap(-1)
        bSizer2.Add(self.lbl_x_mag, 0, wx.ALL, 5)

        self.val_x_mag = wx.TextCtrl(self, wx.ID_ANY, str(self.minimum_width), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.val_x_mag, 0, wx.ALL, 5)

        bSizer1.Add(bSizer2, 1, wx.EXPAND, 5)

        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_y_angle = wx.StaticText(self, wx.ID_ANY, u"y offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_y_angle.Wrap(-1)
        bSizer3.Add(self.lbl_y_angle, 0, wx.ALL, 5)

        self.val_y_angle = wx.TextCtrl(self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer3.Add(self.val_y_angle, 0, wx.ALL, 5)

        bSizer1.Add(bSizer3, 1, wx.EXPAND, 5)

        bSizer8 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_tracks = wx.CheckBox(self, wx.ID_ANY, u"Replicate tracks", wx.DefaultPosition, wx.DefaultSize,
                                         0)
        self.chkbox_tracks.SetValue(True)
        bSizer8.Add(self.chkbox_tracks, 0, wx.ALL, 5)

        bSizer1.Add(bSizer8, 1, wx.EXPAND, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_zones = wx.CheckBox(self, wx.ID_ANY, u"Replicate zones", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_zones.SetValue(True)
        bSizer5.Add(self.chkbox_zones, 0, wx.ALL, 5)

        bSizer1.Add(bSizer5, 1, wx.EXPAND, 5)

        bSizer10 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_intersecting = wx.CheckBox(self, wx.ID_ANY, u"Replicate intersecting tracks/zones",
                                               wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer10.Add(self.chkbox_intersecting, 0, wx.ALL, 5)

        bSizer1.Add(bSizer10, 1, wx.EXPAND, 5)

        bSizer11 = wx.BoxSizer(wx.VERTICAL)

        self.chkbox_remove = wx.CheckBox(self, wx.ID_ANY, u"Remove existing tracks/zones", wx.DefaultPosition,
                                         wx.DefaultSize, 0)

        bSizer11.Add(self.chkbox_remove, 0, wx.ALL, 5)

        bSizer1.Add(bSizer11, 1, wx.EXPAND, 5)

        bSizer12 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_ok = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        self.btn_ok.SetDefault()
        bSizer12.Add(self.btn_ok, 0, wx.ALL, 5)

        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer12.Add(self.btn_cancel, 0, wx.ALL, 5)

        bSizer1.Add(bSizer12, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.coordinate_system.Bind(wx.EVT_RADIOBOX, self.coordinate_system_changed)

    def coordinate_system_changed(self, event):
        # if cartesian
        if self.coordinate_system.GetSelection() == 0:
            self.lbl_x_mag.SetLabelText(u"x offset (mm)")
            self.lbl_y_angle.SetLabelText(u"y offset (mm)")
            self.val_x_mag.SetValue(str(self.minimum_width))
            self.val_y_angle.SetValue(u"0.0")
        else:
            self.lbl_x_mag.SetLabelText(u"radius (mm)")
            self.lbl_y_angle.SetLabelText(u"angle (deg)")
            self.val_x_mag.SetValue(str(self.minimum_radius))
            self.val_y_angle.SetValue(str(self.minimum_angle))
        pass


class ReplicateLayout(pcbnew.ActionPlugin):
    """
    A script to replicate layout
    How to use:
    - move to GAL
    - select module of layout to replicate
    - call the plugin
    - enter pivot step and confirm pivod module
    """

    def defaults(self):
        """
        Method defaults must be redefined
        self.name should be the menu label to use
        self.category should be the category (not yet used)
        self.description should be a comprehensive description
          of the plugin
        """
        self.name = "Replicate layout"
        self.category = "Modify Drawing PCB"
        self.description = "Replicate layout of a hierchical sheet"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        # check if there is exactly one module selected
        selected_modules = filter(lambda x: x.IsSelected(), pcbnew.GetBoard().GetModules())
        selected_names = []
        for mod in selected_modules:
            selected_names.append("{}".format(mod.GetReference()))

        # if exactly one module is selected
        if len(selected_names) == 1:
            process_canceled = False
            # this is a pivot module
            pivot_module_reference = selected_names[0]

            # prepare the replicator
            replicator = replicatelayout.Replicator(pcbnew.GetBoard(), pivot_module_reference)
            # get minimum radius and width
            min_radius = replicator.minimum_radius
            min_width = replicator.minimum_width
            min_angle = replicator.minimum_angle

            # show dialog
            x_offset = None
            y_offset = None
            dlg = ReplicateLayoutDialog(_pcbnew_frame, min_radius, min_width, min_angle)
            res = dlg.ShowModal()

            replicate_containing_only = False
            remove_existing_nets_zones = False
            rep_tracks = False
            rep_zones = False

            if res == wx.ID_OK:
                process_canceled = False
                try:
                    x_offset = float(dlg.val_x_mag.GetValue())
                except:
                    x_offset = None
                try:
                    y_offset = float(dlg.val_y_angle.GetValue())
                except:
                    y_offset = None
                replicate_containing_only = not dlg.chkbox_intersecting.GetValue()
                remove_existing_nets_zones = dlg.chkbox_remove.GetValue()
                rep_tracks = dlg.chkbox_tracks.GetValue()
                rep_zones = dlg.chkbox_zones.GetValue()
            else:
                process_canceled = True

            if process_canceled == False:
                # execute replicate_layout
                if (x_offset != None) and (y_offset != None):
                    # are we replicating in polar coordinate system
                    polar = False
                    if dlg.coordinate_system.GetSelection() != 0:
                        polar = True

                    # replicate now
                    replicator.replicate_layout(x_offset, y_offset,
                                                replicate_containing_only,
                                                remove_existing_nets_zones,
                                                rep_tracks,
                                                rep_zones,
                                                polar)

                    pcbnew.Refresh()
                else:
                    caption = 'Replicate Layout'
                    message = "error parsing x offset and/or y offset input values"
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()

        # if more or less than one show only a messagebox
        else:
            caption = 'Replicate Layout'
            message = "More or less than 1 module selected. Please select exactly one module and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        pass


