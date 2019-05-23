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
import logging
import os
import sys
# import archive_project
if __name__ == '__main__':
    import archive_project
    import archive_project_GUI
else:
    from . import archive_project
    from . import archive_project_GUI

from .archive_project import archive_symbols, archive_3D_models
# import archive_project_GUI
from .archive_project_GUI import ArchiveProjectGUI
SCALE = 1000000.0

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()


class ArchiveProjectDialog (archive_project_GUI.ArchiveProjectGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(ArchiveProjectDialog, self).SetSizeHints(sz1, sz2)
    def __init__(self, parent):
        archive_project_GUI.ArchiveProjectGUI.__init__(self, parent)
        self.Fit()


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
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'library_archive-archive_project.svg.png')

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
                            filename="archive_project.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Archive plugin version: " + VERSION + " started")

        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl

        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl

        # find pcbnew frame
        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]
        # check if eeschema is running
        top_level_windows = wx.GetTopLevelWindows()
        names = []
        for x in top_level_windows:
            names.append(x.GetTitle())
        is_eecshema_open = any('Eeschema' in s for s in names)

        if is_eecshema_open:
            caption = 'Archive project'
            message = "You need to close eeschema and then run the plugin again!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Exiting as eeschema is opened")
            logging.shutdown()
            return

        # show dialog
        main_dialog = ArchiveProjectDialog(_pcbnew_frame)
        main_res = main_dialog.ShowModal()

        if main_res == wx.ID_OK:
            # warn about backing up project before proceeding
            caption = 'Archive project'
            message = "The project should be backed-up before proceeding! \n" \
                      "After succesful archivation, -cache.lib will be deleted!\n" \
                      "The -cache.lib will be reconstruced on the next schematic save event\n" \
                      "All symbols will be available in -archive.lib file!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
        # exit the plugin
        else:
            logger.info("Action plugin canceled on first dialog")
            logging.shutdown()
            return

        if main_dialog.chkbox_sch.GetValue():
            # archive schematics
            try:
                logger.info("Starting schematics archiving")
                archive_project.archive_symbols(board, allow_missing_libraries=False, alt_files=False)
            except (ValueError, IOError, LookupError) as error:
                caption = 'Archive project'
                message = str(error)
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                logger.debug("Action plugin exiting due to error in schematics archiving part")
            except NameError as error:
                caption = 'Archive project'
                message = str(error) + "\nContinue?"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                res = dlg.ShowModal()
                dlg.Destroy()
                logger.info(message)
                if res == wx.ID_YES:
                    logger.info("Retrying schematics archiving")
                    archive_project.archive_symbols(board, allow_missing_libraries=True, alt_files=False)
                else:
                    logging.shutdown()
                    return
            except Exception:
                logger.exception("Fatal error when archiveing schematics")
                caption = 'Archive project'
                message = "Fatal error when archiveing schematics.\n"\
                        + "You can raise an issue on GiHub page.\n" \
                        + "Please attach the net2et_distance.log which you should find in the project folder."
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                logging.shutdown()
                return

            caption = 'Archive project'
            message = "Schematics archived sucessfuly!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()

        if main_dialog.chkbox_3D.GetValue():
            try:
                logger.info("Starting 3D model archiving")
                archive_project.archive_3D_models(board, allow_missing_models=False, alt_files=False)
            except IOError as error:
                caption = 'Archive project'
                message = str(error) + "\nContinue?"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption,  wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                res = dlg.ShowModal()
                dlg.Destroy()
                logger.info(message)
                if res == wx.ID_YES:
                    logger.info("Retrying 3D model archiving")
                    archive_project.archive_3D_models(board, allow_missing_models=True, alt_files=False)
                else:
                    logging.shutdown()
                    return

            caption = 'Archive project'
            message = "3D models archived sucessfuly. Do not forget to save the layout!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            main_dialog.Destroy()
            logging.shutdown()


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
