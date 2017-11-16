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
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Replicate layout", pos=wx.DefaultPosition,
                           size=wx.Size(260, 200), style=wx.DEFAULT_DIALOG_STYLE)

        # self.SetSizeHints(wx.Size(-1, -1), wx.Size(-1, -1))

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_x = wx.StaticText(self, wx.ID_ANY, u"x offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_x.Wrap(-1)
        bSizer2.Add(self.lbl_x, 0, wx.ALL, 5)

        self.val_x = wx.TextCtrl(self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.val_x, 0, wx.ALL, 5)

        bSizer1.Add(bSizer2, 1, wx.EXPAND, 5)

        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.lbl_y = wx.StaticText(self, wx.ID_ANY, u"y offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_y.Wrap(-1)
        bSizer3.Add(self.lbl_y, 0, wx.ALL, 5)

        self.val_y = wx.TextCtrl(self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer3.Add(self.val_y, 0, wx.ALL, 5)

        bSizer1.Add(bSizer3, 1, wx.EXPAND, 5)

        self.chkbox_intersecting = wx.CheckBox(self, wx.ID_ANY, u"Replicate intersecting tracks/zones",
                                               wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer1.Add(self.chkbox_intersecting, 0, wx.ALL, 5)

        bSizer8 = wx.BoxSizer(wx.HORIZONTAL)

        self.chkbox_remove = wx.CheckBox(self, wx.ID_ANY, u"Remove existing tracks/zones", wx.DefaultPosition,
                                         wx.DefaultSize, 0)
        self.chkbox_remove.SetToolTipString(
            u"Remove existing track and zones in the bounding box before and after module placement")

        bSizer8.Add(self.chkbox_remove, 0, wx.ALL, 5)

        bSizer1.Add(bSizer8, 1, wx.EXPAND, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_ok = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        self.btn_ok.SetDefault()
        bSizer5.Add(self.btn_ok, 0, wx.ALL, 5)

        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer5.Add(self.btn_cancel, 0, wx.ALL, 5)

        bSizer1.Add(bSizer5, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)


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

            # show dialog
            x_offset = None
            y_offset = None
            dlg = ReplicateLayoutDialog(_pcbnew_frame)
            res = dlg.ShowModal()
            if res == wx.ID_OK:
                process_canceled = False
                try:
                    x_offset = float(dlg.val_x.GetValue())
                except:
                    x_offset = None
                try:
                    y_offset = float(dlg.val_y.GetValue())
                except:
                    y_offset = None
                replicate_containing_only = not dlg.chkbox_intersecting.GetValue()
                remove_existing_nets_zones = dlg.chkbox_remove.GetValue()
            if res == wx.ID_CANCEL:
                process_canceled = True

            if process_canceled == False:
                # execute replicate_layout
                if (x_offset != None) and (y_offset != None):
                    # prepare to replicate
                    replicator = replicatelayout.Replicator(pcbnew.GetBoard(),
                                                            pivot_module_reference,
                                                            replicate_containing_only)
                    # replicate now
                    replicator.replicate_layout(x_offset, y_offset, remove_existing_nets_zones)

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


