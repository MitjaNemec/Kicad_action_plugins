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
import os
import logging
import sys

if __name__ == '__main__':
    import swap_units
else:
    from . import swap_units

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


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
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'add_component-swap_units.svg.png')

    def Run(self):
        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]
        # check if eeschema is running
        top_level_windows = wx.GetTopLevelWindows()
        names = []
        for x in top_level_windows:
            names.append(x.GetTitle().lower())
        is_eecshema_open = any('eeschema' in s for s in names)

        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="swap_units.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Plugin executed on: " + repr(sys.platform))
        logger.info("Plugin executed with python version: " + repr(sys.version))
        logger.info("KiCad build version: " + BUILD_VERSION)
        logger.info("Swap units plugin version: " + VERSION + " started")

        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl

        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl

        if is_eecshema_open:
            caption = 'Swap units'
            message = "You need to close eeschema and then run the plugin again!"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Action plugin canceled as eeschema was not closed")
            logging.shutdown()
            return

        # load board
        board = pcbnew.GetBoard()

        # check if there are precisely two pads selected
        selected_pads = [x for x in pcbnew.GetBoard().GetPads() if x.IsSelected()]
        if len(selected_pads) != 2:
            caption = 'Swap units'
            message = "More or less than 2 pads selected. Please select exactly two pads and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Action plugin canceled. More or less than 2 pads selected.")
            logging.shutdown()
            return

        # are they on the same module
        pad1 = selected_pads[0]
        pad2 = selected_pads[1]
        if pad1.GetParent().GetReference() != pad2.GetParent().GetReference():
            caption = 'Swap units'
            message = "Pads don't belong to the same footprint"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info("Action plugin canceled. Selected pads don't belong to the same footprint.")
            logging.shutdown()
            return

        # swap pins
        try:
            swap_units.swap(board, pad1, pad2)
            logging.shutdown()
        except LookupError as error:
            caption = 'Swap units'
            message = str(error)
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logger.exception("Gracefully hnadled error while running")
            logging.shutdown()
        except Exception:
            logger.exception("Fatal error when swapping units")
            caption = 'Swap units'
            message = "Fatal error when swapping units.\n"\
                    + "You can raise an issue on GiHub page.\n" \
                    + "Please attach the swap_units.log which you should find in the project folder."
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
