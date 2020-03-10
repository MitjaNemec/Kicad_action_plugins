# -*- coding: utf-8 -*-
#  action_save_restore_layout.py
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
    import save_restore_layout
    import initial_dialog_GUI
    import save_layout_dialog_GUI
else:
    from . import save_restore_layout
    from . import initial_dialog_GUI
    from . import save_layout_dialog_GUI


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
    logging.info("highlighting module: " + repr(module.GetReference()))
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

    def __init__(self, parent, levels, layout_saver, pivot_mod, board):
        save_layout_dialog_GUI.SaveLayoutDialogGUI.__init__(self, parent)

        # clear levels
        self.board = board
        self.board_modules = self.board.GetModules()
        self.pivot_mod = pivot_mod
        self.save_layout = layout_saver
        self.pivot_modules = []
        self.list_levels.Clear()
        self.list_levels.AppendItems(levels)

    def level_changed(self, event):
        # clear highlight on all modules on selected level
        for mod in self.pivot_modules:
            clear_highlight_on_module(mod)
        pcbnew.Refresh()

        # get all pivot modules on selected level
        index = self.list_levels.GetSelection()

        pivot_modules = self.save_layout.layout.get_modules_on_sheet(self.pivot_mod.sheetname[:index+1])
        references = [x.ref for x in pivot_modules]
        self.pivot_modules = []
        for mod in self.board_modules:
            if mod.GetReference() in references:
                self.pivot_modules.append(mod)

        # highlight all modules on selected level
        for mod in self.pivot_modules:
            set_highlight_on_module(mod)
        pcbnew.Refresh()

        event.Skip()

class SaveRestoreLayout(pcbnew.ActionPlugin):
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
        self.name = "Save/Restore Layout"
        self.category = "Modify Drawing PCB"
        self.description = "A plugin to save/restore layout"
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'copy_layout-pcbnew.svg.png')

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
                            filename="save_restore_layout.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Plugin executed on: " + repr(sys.platform))
        logger.info("Plugin executed with python version: " + repr(sys.version))
        logger.info("KiCad build version: " + BUILD_VERSION)
        logger.info("Save/Restore Layout plugin version: " + VERSION + " started")

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
            caption = 'Save/Restore Layout'
            message = "More or less than 1 footprint selected. Please select exactly one footprint and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        # this it the reference footprint
        pivot_module_reference = selected_names[0]

        # ask user which way to select other footprints (by increasing reference number or by ID
        dlg = InitialDialog(_pcbnew_frame)
        res = dlg.ShowModal()

        # save layout
        if res == wx.ID_OK: 
            logger.info("Save layout chosen")

            # prepare the layout to save
            try:
                save_layout = save_restore_layout.SaveLayout(board)
            except Exception:
                logger.exception("Fatal error when creating an instance of SaveLayout")
                caption = 'Save/Restore Layout'
                message = "Fatal error when creating an instance of SaveLayout.\n"\
                        + "You can raise an issue on GiHub page.\n" \
                        + "Please attach the save_restore_layout.log which you should find in the project folder."
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                logging.shutdown()
                return

            # find out the available hierarchical levels
            pivot_mod = save_layout.get_mod_by_ref(pivot_module_reference)
            levels = pivot_mod.filename

            # and show the GUI
            level_dialog = SaveDialog(_pcbnew_frame, levels, save_layout, pivot_mod, board)
            res = level_dialog.ShowModal()

            # clear highlight on all modules on selected level
            for mod in level_dialog.pivot_modules:
                clear_highlight_on_module(mod)
            pcbnew.Refresh()
            if res != wx.ID_OK:
                logging.shutdown()
                return
            index = level_dialog.list_levels.GetSelection()
            # if user did not select any level available cancel
            if index < 0:
                caption = 'Save/Restore Layout'
                message = "One hierarchical level has to be chosen"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                logging.shutdown()
                level_dialog.Destroy()
                return

            # get hierarchy filename to serve as default saved layout filename
            filename = level_dialog.list_levels.GetString(index)
            level_dialog.Destroy()

            # Once user selects a level ask the user top specify file
            wildcard = "Saved Layout Files (*.pckl)|*.pckl"
            dlg = wx.FileDialog(_pcbnew_frame, "Select a file", os.getcwd(), filename.strip(".sch"), wildcard, wx.FD_SAVE)
            res = dlg.ShowModal()
            if res != wx.ID_OK:
                logging.shutdown()
                return
            layout_file = dlg.GetPath()
            dlg.Destroy()

            try:
                save_layout.save_layout(pivot_mod, pivot_mod.sheetname[0:index + 1], layout_file)
            except Exception:
                logger.exception("Fatal error when saving layout")
                caption = 'Save/Restore Layout'
                message = "Fatal error when saving layout.\n"\
                        + "You can raise an issue on GiHub page.\n" \
                        + "Please attach the save_restore_layout.log which you should find in the project folder."
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                logging.shutdown()
                return

        # restore layout
        else:
            logger.info("Restore layout chosen")

            # ask the user to finde the layout information file
            wildcard = "Saved Layout Files (*.pckl)|*.pckl"
            dlg = wx.FileDialog(_pcbnew_frame, "Choose a file", os.getcwd(), "", wildcard, wx.FD_OPEN)
            res = dlg.ShowModal()
            if res != wx.ID_OK:
                logging.shutdown()
                return
            layout_file = dlg.GetPath()
            dlg.Destroy()

            # restore layout
            try:
                restore_layout = save_restore_layout.RestoreLayout(board)
            except Exception:
                logger.exception("Fatal error when creating an instance of RestoreLayout")
                caption = 'Save/Restore Layout'
                message = "Fatal error when creating an instance of RestoreLayout.\n"\
                        + "You can raise an issue on GiHub page.\n" \
                        + "Please attach the save_restore_layout.log which you should find in the project folder."
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                logging.shutdown()
                return

            pivot_mod = restore_layout.get_mod_by_ref(pivot_module_reference)

            try:
                restore_layout.restore_layout(pivot_mod, layout_file)
            except (ValueError, LookupError) as error:
                caption = 'Save/Restore Layout'
                message = str(error)
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                logger.exception("Error when restoring layout") 
                return
            except Exception:
                logger.exception("Fatal error when restoring layout")
                caption = 'Save/Restore Layout'
                message = "Fatal error when restoring layout.\n"\
                        + "You can raise an issue on GiHub page.\n" \
                        + "Please attach the save_restore_layout.log which you should find in the project folder."
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                logging.shutdown()
                return


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
