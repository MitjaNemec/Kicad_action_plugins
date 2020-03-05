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
import os

if __name__ == '__main__':
    import delete_selected_GUI
else:
    from . import delete_selected_GUI

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()
# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"

class DeleteLayoutDialog(delete_selected_GUI.DeleteSelectedGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(DeleteLayoutDialog, self).SetSizeHints(sz1, sz2)

    def __init__(self,  parent):
        delete_selected_GUI.DeleteSelectedGUI.__init__(self, parent)


class DeleteSelected(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - select footprints/tracks/zones to delete
    - call the plugin
    - choose which items to delete
    """

    def defaults(self):
        self.name = "Delete selected"
        self.category = "Modify Drawing PCB"
        self.description = "Delete selected elements"

    def Run(self):
        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]

        # load board
        board = pcbnew.GetBoard()

        # check if there is anything selected
        all_tracks = board.GetTracks()
        selected_tracks = [x for x in all_tracks if x.IsSelected()]

        all_zones = []
        for zoneid in range(board.GetAreaCount()):
            all_zones.append(board.GetArea(zoneid))
        selected_zones = [x for x in all_zones if x.IsSelected()]

        all_modules = board.GetModules()
        selected_modules = [x for x in all_modules if x.IsSelected()]

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

        # if nothing is selected a messagebox
        else:
            caption = 'Delete selected'
            message = "Nothing is selected !"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

        pass
