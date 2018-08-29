# -*- coding: utf-8 -*-
#  action_replicate_layout.py
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
import replicatelayout
import os

___version___ = "1.0"


class ReplicateLayoutDialog(wx.Dialog):
    def __init__(self, parent, replicator):

        self.replicator = replicator

        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Replicate layout", pos=wx.DefaultPosition,
                           size=wx.Size(270, 387), style=wx.DEFAULT_DIALOG_STYLE)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        bSizer111 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_staticText3 = wx.StaticText(self, wx.ID_ANY, u"Hierarchy level:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText3.Wrap(-1)
        self.m_staticText3.SetMinSize(wx.Size(95, -1))

        bSizer111.Add(self.m_staticText3, 0, wx.ALL, 5)

        list_levelsChoices = self.replicator.get_sheet_levels()
        self.list_levels = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, list_levelsChoices, 0 )
        self.list_levels.SetMaxSize(wx.Size(110, -1))
        self.list_levels.SetSelection(len(self.replicator.sheet_levels)-1)


        bSizer111.Add(self.list_levels, 0, wx.ALL, 5)

        bSizer1.Add(bSizer111, 1, wx.EXPAND, 5)

        bSizer9 = wx.BoxSizer(wx.HORIZONTAL)

        self.rad_btn_Linear = wx.RadioButton( self, wx.ID_ANY, u"Linear", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.rad_btn_Linear.SetValue(True)
        bSizer9.Add(self.rad_btn_Linear, 0, wx.ALL, 5)

        self.rad_btn_Circular = wx.RadioButton( self, wx.ID_ANY, u"Circular", wx.DefaultPosition, wx.DefaultSize )
        self.rad_btn_Circular.SetValue(False)
        bSizer9.Add( self.rad_btn_Circular, 0, wx.ALL, 5 )

        bSizer1.Add(bSizer9, 1, wx.EXPAND, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_x_mag = wx.StaticText(self, wx.ID_ANY, u"x offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_x_mag.Wrap(-1)
        self.lbl_x_mag.SetMinSize(wx.Size(95, -1))

        bSizer2.Add(self.lbl_x_mag, 0, wx.ALL, 5)

        self.val_x_mag = wx.TextCtrl(self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0)
        self.val_x_mag.SetMaxSize(wx.Size(110, -1))

        bSizer2.Add(self.val_x_mag, 0, wx.ALL, 5)

        bSizer1.Add(bSizer2, 1, wx.EXPAND, 5)

        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_y_angle = wx.StaticText(self, wx.ID_ANY, u"y offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_y_angle.Wrap(-1)
        self.lbl_y_angle.SetMinSize(wx.Size(95, -1))

        bSizer3.Add(self.lbl_y_angle, 0, wx.ALL, 5)

        self.val_y_angle = wx.TextCtrl(self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0)
        self.val_y_angle.SetMaxSize(wx.Size(110, -1))

        bSizer3.Add(self.val_y_angle, 0, wx.ALL, 5)

        bSizer1.Add(bSizer3, 1, wx.EXPAND, 5)

        bSizer8 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_tracks = wx.CheckBox(self, wx.ID_ANY, u"Replicate tracks", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_tracks.SetValue(True)
        bSizer8.Add(self.chkbox_tracks, 0, wx.ALL, 5)

        bSizer1.Add(bSizer8, 1, wx.EXPAND, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_zones = wx.CheckBox(self, wx.ID_ANY, u"Replicate zones", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_zones.SetValue(True)
        bSizer5.Add(self.chkbox_zones, 0, wx.ALL, 5)

        bSizer1.Add(bSizer5, 1, wx.EXPAND, 5)

        bSizer6 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_text = wx.CheckBox(self, wx.ID_ANY, u"Replicate text", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_text.SetValue(True)
        bSizer6.Add(self.chkbox_text, 0, wx.ALL, 5)

        bSizer1.Add(bSizer6, 1, wx.EXPAND, 5)

        bSizer10 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_intersecting = wx.CheckBox( self, wx.ID_ANY, u"Replicate intersecting tracks/zones", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer10.Add(self.chkbox_intersecting, 0, wx.ALL, 5)

        bSizer1.Add(bSizer10, 1, wx.EXPAND, 5)

        bSizer11 = wx.BoxSizer(wx.VERTICAL)

        self.chkbox_remove = wx.CheckBox( self, wx.ID_ANY, u"Remove existing tracks/zones", wx.DefaultPosition, wx.DefaultSize, 0 )

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
        self.rad_btn_Linear.Bind(wx.EVT_RADIOBUTTON, self.coordinate_system_changed)
        self.rad_btn_Circular.Bind(wx.EVT_RADIOBUTTON, self.coordinate_system_changed)

        self.Bind(wx.EVT_LISTBOX, self.level_changed)

        self.minimum_radius = self.replicator.minimum_radius
        self.minimum_width = self.replicator.minimum_width
        self.minimum_angle = self.replicator.minimum_angle
        self.levels = self.replicator.get_sheet_levels()

        self.val_x_mag.SetValue("%.2f" % self.minimum_width)
        self.val_y_angle.SetValue(u"0.0")

    def level_changed(self, event):
        index = self.list_levels.GetSelection()

        self.replicator.calculate_spacing(self.levels[index])

        self.minimum_radius = self.replicator.minimum_radius
        self.minimum_width = self.replicator.minimum_width
        self.minimum_angle = self.replicator.minimum_angle

        if self.rad_btn_Linear.GetValue():
            self.lbl_x_mag.SetLabelText(u"x offset (mm)")
            self.lbl_y_angle.SetLabelText(u"y offset (mm)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_width)
            self.val_y_angle.SetValue(u"0.0")
        else:
            self.lbl_x_mag.SetLabelText(u"radius (mm)")
            self.lbl_y_angle.SetLabelText(u"angle (deg)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_radius)
            self.val_y_angle.SetValue("%.2f" % self.minimum_angle)
        event.Skip()

    def coordinate_system_changed(self, event):
        # if cartesian
        if self.rad_btn_Linear.GetValue():
            self.rad_btn_Linear.SetValue(True)
            self.rad_btn_Circular.SetValue(False)
            self.lbl_x_mag.SetLabelText(u"x offset (mm)")
            self.lbl_y_angle.SetLabelText(u"y offset (mm)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_width)
            self.val_y_angle.SetValue(u"0.0")
        else:
            self.rad_btn_Linear.SetValue(False)
            self.rad_btn_Circular.SetValue(True)
            self.lbl_x_mag.SetLabelText(u"radius (mm)")
            self.lbl_y_angle.SetLabelText(u"angle (deg)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_radius)
            self.val_y_angle.SetValue("%.2f" % self.minimum_angle)
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
        self.name = "Replicate layout"
        self.category = "Modify Drawing PCB"
        self.description = "Replicate layout of a hierchical sheet"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

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

            sheet_levels = replicator.get_sheet_levels()
            replicator.calculate_spacing(sheet_levels[-1])

            # show dialog
            x_offset = None
            y_offset = None
            dlg = ReplicateLayoutDialog(_pcbnew_frame, replicator)
            res = dlg.ShowModal()

            replicate_containing_only = False
            remove_existing_nets_zones = False
            rep_text = False
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
                rep_text = dlg.chkbox_text.GetValue()
            else:
                process_canceled = True

            if not process_canceled:
                # execute replicate_layout
                if (x_offset is not None) and (y_offset is not None):
                    # are we replicating in polar coordinate system
                    polar = False
                    if dlg.rad_btn_Circular.GetValue():
                        polar = True
                    # failsafe somtimes on my machine wx does not genereta a listbox event
                    index = dlg.list_levels.GetSelection()
                    replicator.calculate_spacing(dlg.levels[index])

                    # replicate now
                    replicator.replicate_layout(x_offset, y_offset,
                                                replicate_containing_only,
                                                remove_existing_nets_zones,
                                                rep_tracks,
                                                rep_zones, rep_text,
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


