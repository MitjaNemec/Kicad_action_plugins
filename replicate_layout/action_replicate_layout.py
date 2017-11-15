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
from pcbnew import *
import replicatelayout

___version___ = "1.0"

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
            # this is a pivot module
            pivot_module_reference = selected_names[0]

            # TODO show a preselected list of sheets which will replicated. Can be edited

            # show dialog to get x and y offsets - should be done with two windows
            caption = 'Replicate Layout'
            message = "Enter x offset in mm"
            dlg = wx.TextEntryDialog(_pcbnew_frame, message, caption, '0.0')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    x_offset = float(dlg.GetValue())
                except:
                    x_offset = None
            else:
                x_offset = None
            dlg.Destroy()

            caption = 'Replicate Layout'
            message = "Enter y offset in mm"
            dlg = wx.TextEntryDialog(_pcbnew_frame, message, caption, '0.0')
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    y_offset = float(dlg.GetValue())
                except:
                    y_offset = None
            else:
                y_offset = None
            dlg.Destroy()
            
            # ask if we want to replicate also tracks and zones that are not completely within the bounding box
            caption = 'Replicate Layout'
            message = "Do you want to replicate also interesecting zones and tracks?"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption,
                                   wx.YES_NO | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_OK:
                replicate_contining_only = True                
            else:
                replicate_contining_only = False    
            dlg.Destroy()

            # execute replicate_layout
            if (x_offset != None) and (y_offset != None):
                # prepare to replicate
                replicator = replicatelayout.Replicator(pcbnew.GetBoard(),
                                                        pivot_module_reference,
                                                        replicate_contining_only)
                # replicate now
                replicator.replicate_layout(x_offset, y_offset)

                pcbnew.Refresh()
            else:
                caption = 'Replicate Layout'
                message = "error parsing x offset and/or y offset input values" % (x_offset, y_offset)
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


