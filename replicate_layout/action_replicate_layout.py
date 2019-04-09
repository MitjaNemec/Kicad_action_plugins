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
from __future__ import absolute_import, division, print_function
import wx
import pcbnew
import os
import logging
import sys

if __name__ == '__main__':
    import replicatelayout
    import replicate_layout_GUI
else:
    from . import replicatelayout
    from . import replicate_layout_GUI

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()


class ReplicateLayoutDialog(replicate_layout_GUI.ReplicateLayoutGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO NOTHING
        pass

    def __init__(self, parent, replicator, mod_ref):
        replicate_layout_GUI.ReplicateLayoutGUI.__init__(self, parent)

        # Connect Events
        self.Bind(wx.EVT_LISTBOX, self.level_changed, id=26)

        self.replicator = replicator
        self.pivot_mod = self.replicator.get_mod_by_ref(mod_ref)
        self.levels = self.pivot_mod.filename

        # clear levels
        self.list_levels.Clear()
        self.list_levels.AppendItems(self.levels)

    def level_changed(self, event):
        index = self.list_levels.GetSelection()

        list_sheetsChoices = self.replicator.get_sheets_to_replicate(self.pivot_mod, self.pivot_mod.sheet_id[index])

        # get anchor modules
        anchor_modules = self.replicator.get_list_of_modules_with_same_id(self.pivot_mod.mod_id)
        # find matching anchors to maching sheets
        ref_list = []
        for sheet in list_sheetsChoices:
            for mod in anchor_modules:
                if "/".join(sheet) in "/".join(mod.sheet_id):
                    ref_list.append(mod.ref)
                    break

        sheets_for_list = [('/').join(x[0]) + " (" + x[1] + ")" for x in zip(list_sheetsChoices, ref_list)]
        # clear levels
        self.list_sheets.Clear()
        self.list_sheets.AppendItems(sheets_for_list)

        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)

        event.Skip()


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
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'duplicate-replicate_layout.svg.png')

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="replicate_layout.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Replicate layout plugin version: " + VERSION + " started")

        stdout_logger = logging.getLogger('STDOUT')
        sl_out = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl_out

        stderr_logger = logging.getLogger('STDERR')
        sl_err = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl_err

        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]

        # check if there is exactly one module selected
        selected_modules = [x for x in pcbnew.GetBoard().GetModules() if x.IsSelected()]
        selected_names = []
        for mod in selected_modules:
            selected_names.append("{}".format(mod.GetReference()))

        # if more or less than one show only a messagebox
        if len(selected_names) != 1:
            caption = 'Replicate Layout'
            message = "More or less than 1 module selected. Please select exactly one module and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        # if exactly one module is selected
        # this is a pivot module
        pivot_module_reference = selected_names[0]

        # prepare the replicator
        logger.info("Preparing replicator with " + pivot_module_reference + " as a reference")

        replicator = replicatelayout.Replicator(board)
        pivot_mod = replicator.get_mod_by_ref(pivot_module_reference)

        logger.info("Pivot module is %s\nLocated on:%s\nWith filenames:%s\nWith sheet_id:%s" \
                    % (repr(pivot_mod.ref), repr(pivot_mod.sheet_id), repr(pivot_mod.filename), repr(pivot_mod.sheet_id)))

        list_of_modules_with_same_id = replicator.get_list_of_modules_with_same_id(pivot_mod.mod_id)
        nice_list = [(x.ref, x.sheet_id) for x in list_of_modules_with_same_id]
        logger.info("Corresponding modules are \n%s" % repr(nice_list))

        list_of_modules = replicator.get_list_of_modules_with_same_id(pivot_mod.mod_id)
        if not list_of_modules:
            caption = 'Replicate Layout'
            message = "Selected module is uniqe in the pcb (only one module with this ID)"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # show dialog
        logger.info("Showing dialog")
        dlg = ReplicateLayoutDialog(_pcbnew_frame, replicator, pivot_module_reference)
        res = dlg.ShowModal()

        if res == wx.ID_OK:

            selected_items = dlg.list_sheets.GetSelections()
            slected_names = []
            for sel in selected_items:
                slected_names.append(dlg.list_sheets.GetString(sel))

            replicate_containing_only = not dlg.chkbox_intersecting.GetValue()
            remove_existing_nets_zones = dlg.chkbox_remove.GetValue()
            rep_tracks = dlg.chkbox_tracks.GetValue()
            rep_zones = dlg.chkbox_zones.GetValue()
            rep_text = dlg.chkbox_text.GetValue()
            rep_drawings = dlg.chkbox_drawings.GetValue()
        else:
            logger.info("User canceled the dialog")
            return

        # failsafe somtimes on my machine wx does not generate a listbox event
        level = dlg.list_levels.GetSelection()
        selection_indeces = dlg.list_sheets.GetSelections()
        sheets_on_a_level = replicator.get_sheets_to_replicate(pivot_mod, pivot_mod.sheet_id[level])
        sheets_for_replication = [sheets_on_a_level[i] for i in selection_indeces]

        # replicate now
        logger.info("Replicating layout")

        try:
            replicator.replicate_layout(pivot_mod, pivot_mod.sheet_id[0:level+1], sheets_for_replication,
                                        containing=replicate_containing_only,
                                        remove=remove_existing_nets_zones,
                                        tracks=rep_tracks,
                                        zones=rep_zones,
                                        text=rep_text,
                                        drawings=rep_drawings)
            logger.info("Replication complete")
            pcbnew.Refresh()
        except Exception:
            logger.exception("Fatal error when replicating")
            raise


class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self, *args, **kwargs):
        """No-op for wrapper"""
        pass