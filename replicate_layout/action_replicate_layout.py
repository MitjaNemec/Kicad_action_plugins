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
import time

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

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


def set_highlight_on_module(module):
    pads_list = module.Pads()
    for pad in pads_list:
        pad.SetBrightened()
    drawings = module.GraphicalItems()
    for item in drawings:
        item.SetBrightened()


def clear_highlight_on_module(module):
    pads_list = module.Pads()
    for pad in pads_list:
        pad.ClearBrightened()
    drawings = module.GraphicalItems()
    for item in drawings:
        item.ClearBrightened()


class ReplicateLayoutDialog(replicate_layout_GUI.ReplicateLayoutGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO NOTHING
        pass

    def __init__(self, parent, replicator, mod_ref, logger):
        replicate_layout_GUI.ReplicateLayoutGUI.__init__(self, parent)

        # Connect Events
        self.Bind(wx.EVT_LISTBOX, self.level_changed, id=26)

        self.logger = logger

        self.replicator = replicator
        self.src_anchor_module = self.replicator.get_mod_by_ref(mod_ref)
        self.levels = self.src_anchor_module.filename

        # clear levels
        self.list_levels.Clear()
        self.list_levels.AppendItems(self.levels)

        self.src_modules = []

    def level_changed(self, event):

        index = self.list_levels.GetSelection()
        list_sheetsChoices = self.replicator.get_sheets_to_replicate(self.src_anchor_module, self.src_anchor_module.sheet_id[index])

        # clear highlight on all modules on selected level
        for mod in self.src_modules:
            clear_highlight_on_module(mod)
        pcbnew.Refresh()

        # get anchor modules
        anchor_modules = self.replicator.get_list_of_modules_with_same_id(self.src_anchor_module.mod_id)
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

        # get all source modules on selected level
        src_modules = self.replicator.get_modules_on_sheet(self.src_anchor_module.sheet_id[:index + 1])
        self.src_modules = [x.mod for x in src_modules]

        # highlight all modules on selected level
        for mod in self.src_modules:
            set_highlight_on_module(mod)
        pcbnew.Refresh()

        event.Skip()

    def OnOk(self, event):
        selected_items = self.list_sheets.GetSelections()
        slected_names = []
        for item in selected_items:
            slected_names.append(self.list_sheets.GetString(item))

        # grab checkboxes
        replicate_containing_only = not self.chkbox_intersecting.GetValue()
        remove_existing_nets_zones = self.chkbox_remove.GetValue()
        rep_tracks = self.chkbox_tracks.GetValue()
        rep_zones = self.chkbox_zones.GetValue()
        rep_text = self.chkbox_text.GetValue()
        rep_drawings = self.chkbox_drawings.GetValue()
        remove_duplicates = self.chkbox_remove_duplicates.GetValue()
        rep_locked = self.chkbox_locked.GetValue()

        # failsafe somtimes on my machine wx does not generate a listbox event
        level = self.list_levels.GetSelection()
        selection_indeces = self.list_sheets.GetSelections()
        sheets_on_a_level = self.replicator.get_sheets_to_replicate(self.src_anchor_module, self.src_anchor_module.sheet_id[level])
        dst_sheets = [sheets_on_a_level[i] for i in selection_indeces]

        # check if all the destination anchor footprints are on the same layer as source anchorfootprint
        # first get all the anchor footprints
        all_dst_modules = []
        for sheet in dst_sheets:
            all_dst_modules.extend(self.replicator.get_modules_on_sheet(sheet))
        dst_anchor_modules = [x for x in all_dst_modules if x.mod_id == self.src_anchor_module.mod_id]

        # then check if all of them are on the same layer
        if not all(self.src_anchor_module.mod.IsFlipped() == mod.mod.IsFlipped() for mod in dst_anchor_modules):
            # clear highlight on all modules on selected level
            for mod in self.src_modules:
                clear_highlight_on_module(mod)
            pcbnew.Refresh()

            caption = 'Replicate Layout'
            message = "Destination anchor footprints must be on the same layer as source anchor footprint!"
            dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            self.Destroy()
            return

        # replicate now
        self.logger.info("Replicating layout")

        self.start_time = time.time()
        self.last_time = self.start_time
        self.progress_dlg = wx.ProgressDialog("Preparing for replication", "Starting plugin", maximum=100)
        self.progress_dlg.Show()
        self.progress_dlg.ToggleWindowStyle(wx.STAY_ON_TOP)
        self.Hide()

        try:
            # update progress dialog 
            self.replicator.update_progress = self.update_progress
            self.replicator.replicate_layout(self.src_anchor_module, self.src_anchor_module.sheet_id[0:level + 1], dst_sheets,
                                             containing=replicate_containing_only,
                                             remove=remove_existing_nets_zones,
                                             tracks=rep_tracks,
                                             zones=rep_zones,
                                             text=rep_text,
                                             drawings=rep_drawings,
                                             rm_duplicates=remove_duplicates,
                                             rep_locked=rep_locked)

            self.logger.info("Replication complete")
            # clear highlight on all modules on selected level
            for mod in self.src_modules:
                clear_highlight_on_module(mod)
            pcbnew.Refresh()

            logging.shutdown()
            self.progress_dlg.Destroy()
            self.Destroy()
        except LookupError as exception:
            # clear highlight on all modules on selected level
            for mod in self.src_modules:
                clear_highlight_on_module(mod)
            pcbnew.Refresh()

            caption = 'Replicate Layout'
            message = str(exception)
            dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            self.progress_dlg.Destroy()
            self.Destroy()
            return
        except Exception:
            # clear highlight on all modules on selected level
            for mod in self.src_modules:
                clear_highlight_on_module(mod)
            pcbnew.Refresh()

            self.logger.exception("Fatal error when running replicator")
            caption = 'Replicate Layout'
            message = "Fatal error when running replicator.\n"\
                    + "You can raise an issue on GiHub page.\n" \
                    + "Please attach the replicate_layout.log which you should find in the project folder."
            dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            self.progress_dlg.Destroy()
            self.Destroy()
            return

        event.Skip()

    def OnCancel(self, event):
        # clear highlight on all modules on selected level
        for mod in self.src_modules:
            clear_highlight_on_module(mod)
        pcbnew.Refresh()

        self.logger.info("User canceled the dialog")
        logging.shutdown()
        event.Skip()

    def update_progress(self, stage, percentage, message=None):
        current_time = time.time()
        # update GUI onle every 10 ms
        i = int(percentage*100)
        if message is not None:
            logging.info("updating GUI message: " + repr(message))
            self.progress_dlg.Update(i, message)
        if (current_time - self.last_time) > 0.01:
            self.last_time = current_time
            delta_time = self.last_time - self.start_time
            logging.info("updating GUI with: " + repr(i))
            self.progress_dlg.Update(i)


class ReplicateLayout(pcbnew.ActionPlugin):
    """
    A script to replicate layout
    How to use:
    - move to GAL
    - select footprint of layout to replicate
    - call the plugin
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

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="replicate_layout.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        
        logger.info("Plugin executed on: " + repr(sys.platform))
        logger.info("Plugin executed with python version: " + repr(sys.version))
        logger.info("KiCad build version: " + BUILD_VERSION)
        logger.info("Replicate layout plugin version: " + VERSION + " started")

        stdout_logger = logging.getLogger('STDOUT')
        sl_out = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl_out

        stderr_logger = logging.getLogger('STDERR')
        sl_err = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl_err

        # for solving an issue #99
        logger.info("wx top level windows: " +repr(wx.GetTopLevelWindows()))

        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]

        # check if there is exactly one module selected
        selected_modules = [x for x in pcbnew.GetBoard().GetModules() if x.IsSelected()]
        selected_names = []
        for mod in selected_modules:
            selected_names.append("{}".format(mod.GetReference()))

        # if more or less than one show only a messagebox
        if len(selected_names) != 1:
            caption = 'Replicate Layout'
            message = "More or less than 1 footprints selected. Please select exactly one footprint and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return
        # if exactly one module is selected
        # this is a source anchor module
        src_anchor_mod_reference = selected_names[0]

        # prepare the replicator
        logger.info("Preparing replicator with " + src_anchor_mod_reference + " as a reference")

        try:
            replicator = replicatelayout.Replicator(board)
        except LookupError as exception:
            caption = 'Replicate Layout'
            message = str(exception)
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return
        except Exception:
            logger.exception("Fatal error when making an instance of replicator")
            caption = 'Replicate Layout'
            message = "Fatal error when making an instance of replicator.\n"\
                    + "You can raise an issue on GiHub page.\n" \
                    + "Please attach the replicate_layout.log which you should find in the project folder."
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        src_anchor_module = replicator.get_mod_by_ref(src_anchor_mod_reference)

        logger.info("source anchor footprint is %s\nLocated on:%s\nWith filenames:%s\nWith sheet_id:%s" \
                    % (repr(src_anchor_module.ref), repr(src_anchor_module.sheet_id), repr(src_anchor_module.filename), repr(src_anchor_module.sheet_id)))

        dst_anchor_modules = replicator.get_list_of_modules_with_same_id(src_anchor_module.mod_id)
        nice_list = [(x.ref, x.sheet_id) for x in dst_anchor_modules]
        logger.info("Corresponding footprints are \n%s" % repr(nice_list))

        list_of_modules = replicator.get_list_of_modules_with_same_id(src_anchor_module.mod_id)
        if not list_of_modules:
            caption = 'Replicate Layout'
            message = "Selected footprint is uniqe in the pcb (only one footprint with this ID)"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        # show dialog
        logger.info("Showing dialog")
        dlg = ReplicateLayoutDialog(_pcbnew_frame, replicator, src_anchor_mod_reference, logger)
        # find pcbnew position
        pcbnew_pos = _pcbnew_frame.GetScreenPosition()
        logger.info("Pcbnew position: " + repr(pcbnew_pos))

        # find all the display sizes
        display = list()
        for n in range(wx.Display.GetCount()):
            display.append(wx.Display(n).GetGeometry())
            logger.info("Display " + repr(n) + ": " + repr(wx.Display(n).GetGeometry()))

        # find position of right toolbar
        toolbar_pos = _pcbnew_frame.FindWindowById(pcbnew.ID_V_TOOLBAR).GetScreenPosition()
        logger.info("Toolbar position: " + repr(toolbar_pos))
        # caluclate absolute

        # find site of dialog
        size = dlg.GetSize()
        # calculate the position
        dialog_position = wx.Point(toolbar_pos[0] - size[0], toolbar_pos[1])
        logger.info("Dialog position: " + repr(dialog_position))
        dlg.SetPosition(dialog_position)
        dlg.Show()

        # clear highlight on all modules on selected level
        for mod in dlg.src_modules:
            clear_highlight_on_module(mod)
        pcbnew.Refresh()


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