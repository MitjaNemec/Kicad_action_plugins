#  action_swap_pins.py
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
import swap_units
import os
import logging
import sys


class SwapUnits(pcbnew.ActionPlugin):
    """
    A script to swap selected pins
    How to use:
    - move to GAL
    - select pads with same function on two different units within same footprint to swap
    - call the plugin
    """

    def defaults(self):
        self.name = "Swap units"
        self.category = "Modify Drawing PCB and schematics"
        self.description = "Swap selected units"

    def Run(self):
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

        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="swap_units.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S',
                            disable_existing_loggers=False)
        logger = logging.getLogger(__name__)
        logger.info("Action plugin Swap units started")

        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl

        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl

        if is_eecshema_open:
            caption = 'Swap pins'
            message = "You need to close eeschema and then run the plugin again!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Action plugin canceled as eeschema was not closed")
            return

        # load board
        board = pcbnew.GetBoard()
                    
        # check if there are precisely two pads selected
        selected_pads = filter(lambda x: x.IsSelected(), pcbnew.GetBoard().GetPads())
        if len(selected_pads) != 2:
            caption = 'Swap pins'
            message = "More or less than 2 pads selected. Please select exactly two pads and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Action plugin canceled. More or less than 2 pads selected.")
            return

        # are they on the same module
        pad1 = selected_pads[0]
        pad2 = selected_pads[1]
        if pad1.GetParent().GetReference() != pad2.GetParent().GetReference():
            caption = 'Swap pins'
            message = "Pads don't belong to the same footprint"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Action plugin canceled. Selected pads don't belong to the same footprint.")
            return

        # swap pins
        try:
            swap_units.swap(board, pad1, pad2)
        except Exception:
            logger.exception("Fatal error when swapping units")
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
