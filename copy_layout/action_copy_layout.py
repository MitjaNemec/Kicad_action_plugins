# -*- coding: utf-8 -*-
#  action_replicate_layout.py
#
# Copyright (C) 2019 Mitja Nemec
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
import logging
import sys

# import place_footprints
if __name__ == '__main__':
    import copy_layout
    import initial_dialog_GUI
    import save_layout_dialog_GUI
else:
    from . import copy_layout
    from . import initial_dialog_GUI
    from . import save_layout_dialog_GUI


# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()


class InitialDialog(initial_dialog_GUI.InitialDialogGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO NOTHING
        pass

    def __init__(self, parent):
        initial_dialog_GUI.InitialDialogGUI.__init__(self, parent)


class SaveDialog(save_layout_dialog_GUI.SaveLayoutDialogGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO NOTHING
        pass

    def __init__(self, parent, levels):
        save_layout_dialog_GUI.SaveLayoutDialogGUI.__init__(self, parent)
        
        # clear levels
        self.list_levels.Clear()
        self.list_levels.AppendItems(levels)

class CopyLayout(pcbnew.ActionPlugin):
    """
    A plugin to save/restore layout
    How to save layout:
    - select footprint of hierarchical sheet layout to replicate
    - run the plugin, select which hirarchical level to save
    - select filename where to save the layout information
    How to restore layout:
    - select the footprint which will save as an anchor point
    - run the plugin, choose the file from which to restore the layout
    """

    def defaults(self):
        self.name = "Copy layout"
        self.category = "Modify Drawing PCB"
        self.description = "A plugin to save/restore layout"
        #self.icon_file_name = os.path.join(
        #        os.path.dirname(__file__), 'array-place_footprints.svg.png')

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="copy_layout.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Copy layout plugin version: " + VERSION + " started")

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
            caption = 'Copy layout'
            message = "More or less than 1 footprint selected. Please select exactly one footprint and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # this it the reference footprint
        pivot_module_reference = selected_names[0]

        # ask user which way to select other footprints (by increasing reference number or by ID
        dlg = InitialDialog(_pcbnew_frame)
        res = dlg.ShowModal()

        # save layout
        if res == wx.ID_OK:
            # show the gui and wait for user to select the hierarchical level which to save
            
            # i should create a copy of a board and then work on a copy of the board, and finally i Should delete it
            # but I don't know how to move this into class

            save_layout = copy_layout.SaveLayout(board)

            pivot_mod = save_layout.get_mod_by_ref(pivot_module_reference)
            levels = pivot_mod.filename
            level_dialog = SaveDialog(_pcbnew_frame, levels)
            res = level_dialog.ShowModal()
            if res != wx.ID_OK:
                return
            index = level_dialog.list_levels.GetSelection()
            level_dialog.Destroy()

            # ask the user top specify file
            wildcard = "Saved Layout Files (*.pckl)|*.pckl"
            dlg = wx.FileDialog(_pcbnew_frame, "Select a file", os.getcwd(), "", wildcard, wx.SAVE)
            res = dlg.ShowModal()
            if res != wx.ID_OK:
                return
            layout_file = dlg.GetPath()
            dlg.Destroy()

            layout_file = save_layout.export_layout(pivot_mod, pivot_mod.sheetname[0:index+1], layout_file)

        # restore layout
        else:
            # ask the user to finde the layout information file
            wildcard = "Saved Layout Files (*.pckl)|*.pckl"
            dlg = wx.FileDialog(_pcbnew_frame, "Choose a file", os.getcwd(), "", wildcard, wx.OPEN)
            res = dlg.ShowModal()
            if res != wx.ID_OK:
                return
            layout_file = dlg.GetPath()
            dlg.Destroy()

            # restore layout
            restore_layout = copy_layout.RestoreLayout(board)

            pivot_mod = restore_layout.get_mod_by_ref(pivot_module_reference)

            restore_layout.import_layout(pivot_mod, layout_file)

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
