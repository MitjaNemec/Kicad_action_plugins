#  action_net2net_min_distance.py
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

if __name__ == '__main__':
    import net2net_distance
else:
    from . import net2net_distance
SCALE = 1000000.0

# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


class Net2NedDistance(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - select two pads
    - call the plugin
    """

    def defaults(self):
        self.name = "Net2Net distance"
        self.category = "Measure distance"
        self.description = "Measure minimum distance between two selected nets"

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # get user units
        if pcbnew.GetUserUnits() == 1:
            user_units = 'mm'
        else:
            user_units = 'in'

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="net2net_distance.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Plugin executed on: " + repr(sys.platform))
        logger.info("Plugin executed with python version: " + repr(sys.version))
        logger.info("KiCad build version: " + BUILD_VERSION)
        logger.info("Net2net distance plugin version: " + VERSION + " started")

        stdout_logger = logging.getLogger('STDOUT')
        sl_out = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl_out

        stderr_logger = logging.getLogger('STDERR')
        sl_err = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl_err

        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]

        # get all selected nets either as tracks or as pads
        nets = set()
        selected_tracks = [x for x in board.GetTracks() if x.IsSelected()]

        nets.update([track.GetNetname() for track in selected_tracks])

        modules = board.GetModules()
        for mod in modules:
            pads = mod.Pads()
            nets.update([pad.GetNetname() for pad in pads if pad.IsSelected()])

        # if two pads are selected
        if len(nets) != 2:
            # if more or less than one show only a messagebox
            caption = 'Net2Net Distance'
            message = "You have to select two and only two nets"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        try:
            dis, loc = net2net_distance.get_min_distance(board, list(nets))
        except Exception:
            logger.exception("Fatal error running net2net_min_distance")
            caption = 'Net2Net Track Distance'
            message = "Fatal error when replicating.\n"\
                    + "You can raise an issue on GiHub page.\n" \
                    + "Please attach the net2et_distance.log which you should find in the project folder."
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return
            
        caption = 'Net2Net Track Distance'
        if user_units == 'mm':
            message = "Minimum distance between net segments is " + "%.3f" % (dis/SCALE) + " mm"
        else:
            message = "Minimum distance between net segments is " + "%.4f" % (dis/(SCALE*25.4)) + " in"
        dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
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
