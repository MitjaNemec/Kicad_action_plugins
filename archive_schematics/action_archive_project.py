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

        # notify the user to close the schematics
        # if possible chech if schematics is open. If it is, close it if possible
                # pcbnew.Refresh()
        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

