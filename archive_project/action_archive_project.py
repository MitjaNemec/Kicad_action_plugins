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
import logging
import os
import sys


SCALE = 1000000.0


class ArchiveProjectDialog (wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Archive project", pos=wx.DefaultPosition,
                           style=wx.DEFAULT_DIALOG_STYLE)

        bSizer4 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText2 = wx.StaticText(self, wx.ID_ANY, u"Archive project:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        bSizer4.Add(self.m_staticText2, 0, wx.ALL, 5)

        self.chkbox_sch = wx.CheckBox(self, wx.ID_ANY, u"Archive Schematics", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_sch.SetValue(True)
        bSizer4.Add(self.chkbox_sch, 0, wx.ALL, 5)

        self.chkbox_3D = wx.CheckBox(self, wx.ID_ANY, u"Archive 3D models", wx.DefaultPosition, wx.DefaultSize, 0)
        self.chkbox_3D.SetValue(True)
        bSizer4.Add(self.chkbox_3D, 0, wx.ALL, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_button3 = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer5.Add(self.m_button3, 0, wx.ALL, 5)

        self.m_button4 = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer5.Add(self.m_button4, 0, wx.ALL, 5)

        bSizer4.Add(bSizer5, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer4)
        self.Layout()

        self.Centre(wx.BOTH)

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

    def Run(self):
        # load board
        board = pcbnew.GetBoard()
        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="archive_project.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S',
                            disable_existing_loggers=False)
        logger = logging.getLogger(__name__)
        logger.info("Action plugin started")

        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl

        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl

        # find pcbnew frame
        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().startswith('Pcbnew'),
                   wx.GetTopLevelWindows()
                   )[0]
        # check if eeschema is running
        top_level_windows = wx.wx.GetTopLevelWindows()
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
            return

        # only testing if keypress simulation works
        key_simulator = wx.UIActionSimulator()

        # show dialog
        main_dialog = ArchiveProjectDialog(_pcbnew_frame)
        main_res = main_dialog.ShowModal()

        if main_res == wx.ID_OK:
            # warn about backing up project before proceeding
            caption = 'Archive project'
            message = "The project should be backed-up before proceeding"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
        # exit the plugin
        else:
            logger.info("Action plugin canceled on first dialog")
            return

        # if user clicked OK
        if main_res == wx.ID_OK:
            if main_dialog.chkbox_sch.GetValue():
                # archive schematics
                try:
                    logger.info("Starting schematics archiving")
                    archive_project.archive_symbols(board, allow_missing_libraries=False, alt_files=False)
                except (ValueError, IOError, LookupError), error:
                    caption = 'Archive project'
                    message = str(error)
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_EXCLAMATION)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logger.debug("Action plugin exiting due to error in schematics archiving part")
                except NameError as error:
                    caption = 'Archive project'
                    message = str(error)+ "\nContinue?"
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                    res = dlg.ShowModal()
                    dlg.Destroy()
                    logger.info(message)
                    if res == wx.ID_YES:
                        logger.info("Retrying schematics archiving")
                        archive_project.archive_symbols(board, allow_missing_libraries=True, alt_files=False)
                    else:
                        return

            if main_dialog.chkbox_3D.GetValue():

                filename = board.GetFileName()

                caption = 'Archive project'
                message = "Current layout will be saved and when the plugin finishes, pcbnew will be closed." \
                          "This is normal behaviour.\n" \
                          "\nProceed?"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                res = dlg.ShowModal()
                dlg.Destroy()

                if res == wx.ID_NO:
                    return

                # simulate Ctrl+S (save layout)
                key_simulator.KeyDown(wx.WXK_CONTROL_S, wx.MOD_CONTROL)
                key_simulator.KeyUp(wx.WXK_CONTROL_S, wx.MOD_CONTROL)

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
                        # simulate Ctrl+S (save layout)
                        key_simulator.KeyDown(wx.WXK_CONTROL_S, wx.MOD_CONTROL)
                        key_simulator.KeyUp(wx.WXK_CONTROL_S, wx.MOD_CONTROL)

                        archive_project.archive_3D_models(board, allow_missing_models=True, alt_files=False)
                    else:
                        return

                caption = 'Archive project'
                message = "The project finished succesfully. Exiting pcbnew"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_QUESTION)
                dlg.ShowModal()
                dlg.Destroy()

                logger.info("3D model linking successful, exiting pcbnew")

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

                # tab
                key_simulator.KeyDown(wx.WXK_TAB)
                key_simulator.KeyUp(wx.WXK_TAB)

                # enter
                key_simulator.KeyDown(wx.WXK_RETURN)
                key_simulator.KeyUp(wx.WXK_RETURN)

            main_dialog.Destroy()


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
