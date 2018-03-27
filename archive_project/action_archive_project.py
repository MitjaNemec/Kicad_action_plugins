#  action_archive_schematics.py
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
import archive_project



SCALE = 1000000.0


class ArchiveProject(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - call the plugin
    """

    def defaults(self):
        self.name = "Archive project"
        self.category = "Archive project"
        self.description = "Archive schematics symbols and 3D models"

    def Run(self):
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]

        # only testing if keypress simulation works

        key_simulator = wx.UIActionSimulator()

        # show the dialog informing the user that eeschema should be closed
        caption = 'Archive project'
        message = "Is eeschema closed?"
        dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res == wx.ID_NO:
            caption = 'Archive project'
            message = "You need to close eeschema and then run the plugin again!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        caption = 'Archive project'
        message = "Current layout will be saved and when the plugin finishes, pcbnew will be closed." \
                  "This is normal behaviour.\n" \
                  "You should back up the project before proceeding any further\n" \
                  "\nProceed?"
        dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()

        if res == wx.ID_NO:
            return

        # simulate Ctrl+S (save layout)
        key_simulator.KeyDown(wx.WXK_CONTROL_S, wx.MOD_CONTROL)
        key_simulator.KeyUp(wx.WXK_CONTROL_S, wx.MOD_CONTROL)

        # archive the project

        # exit pcbnew to avoid issues with concurent editing of .kicad_pcb file
        # simulate Alt+F (File) and e twice (Exit) and Enter
        key_simulator.KeyDown(ord('f'), wx.MOD_ALT)
        key_simulator.KeyUp(ord('f'), wx.MOD_ALT)

        key_simulator.KeyDown(ord('e'))
        key_simulator.KeyUp(ord('e'))

        key_simulator.KeyDown(ord('e'))
        key_simulator.KeyUp(ord('e'))
        
        key_simulator.KeyDown(wx.WXK_RETURN)
        key_simulator.KeyUp(wx.WXK_RETURN)

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

