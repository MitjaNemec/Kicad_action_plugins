# -*- coding: utf-8 -*-
#  action_pad2pad_track_distance.py
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
    import pad2pad_track_distance
    import pad2pad_track_distance_GUI
else:
    from . import pad2pad_track_distance
    from . import pad2pad_track_distance_GUI

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


class Pad2PadTrackDistanceDialog(pad2pad_track_distance_GUI.Pad2PadTrackDistanceGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(Pad2PadTrackDistanceDialog, self).SetSizeHints(sz1, sz2)

    def __init__(self, parent, all_tracks, selected_tracks, logger):
        pad2pad_track_distance_GUI.Pad2PadTrackDistanceGUI.__init__(self, parent)
        self.Fit()
        self.all_tracks = all_tracks
        self.selected_tracks = selected_tracks
        self.logger = logger

    def highlight_tracks(self, event):
        self.logger.info("Highligting tracks")
        for track in self.selected_tracks:
            track.SetBrightened()
        pcbnew.Refresh()
        event.Skip()

    def on_btn_ok(self, event):
        self.logger.info("Removing highligting")
        for track in self.selected_tracks:
            track.ClearBrightened()
        pcbnew.Refresh()
        logging.shutdown()
        event.Skip()


class Pad2PadTrackDistance(pcbnew.ActionPlugin):
    """
    A script to delete selection
    How to use:
    - move to GAL
    - select two pads
    - call the plugin
    """

    def defaults(self):
        self.name = "Pad2Pad distance"
        self.category = "Measure distance"
        self.description = "Measure distance between two selected pads"
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'ps_tune_length-pad2pad_track_distance.svg.png')

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
                            filename="pad2pad_track_distance.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Plugin executed on: " + repr(sys.platform))
        logger.info("Plugin executed with python version: " + repr(sys.version))
        logger.info("KiCad build version: " + BUILD_VERSION)
        logger.info("Length stats plugin version: " + VERSION + " started")

        stdout_logger = logging.getLogger('STDOUT')
        sl_out = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl_out

        stderr_logger = logging.getLogger('STDERR')
        sl_err = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl_err

        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]

        # get user units
        if pcbnew.GetUserUnits() == 1:
            user_units = 'mm'
        else:
            user_units = 'in'

        # get all pads
        modules = board.GetModules()

        pads = []
        for mod in modules:
            # get their pads
            module_pads = mod.Pads()
            # get net
            for pad in module_pads:
                pads.append(pad)

        # get list of all selected pads
        selected_pads = []
        for pad in pads:
            if pad.IsSelected():
                selected_pads.append(pad)

        # check the nets on all the pads
        nets = []
        for pad in selected_pads:
            nets.append(pad.GetNetname())

        # if more or less than two pads are selected
        if len(selected_pads) != 2:
            caption = 'Pad2Pad Track Distance'
            message = "You have to select two and only two pads"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        # and if they are on different nest
        if nets[0] != nets[1]:
            caption = 'Pad2Pad Track Distance'
            message = "The selected pads are not on the same net"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        try:
            measure_distance = pad2pad_track_distance.Distance(board, selected_pads[0], selected_pads[1])
            distance, resistance = measure_distance.get_length()
        except LookupError as error:
            caption = 'Pad2Pad Track Distance'
            message = str(error) 
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logger.info(message)
            logging.shutdown()
            return
        except Exception:
            logger.exception("Fatal error when measuring")
            caption = 'Pad2Pad Track Distance'
            message = "Fatal error when measuring.\n"\
                    + "You can raise an issue on GiHub page.\n" \
                    + "Please attach the pad2pad_track_distance.log which you should find in the project folder."
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        # trying to show in layout which tracks are taken into account - so far it does not work
        # as the selection is automatically cleared when exiting action plugin
        # I'll leave this code in just for reference
        selected_pads[0].ClearSelected()
        selected_pads[1].ClearSelected()

        # deselect all tracks except used ones
        all_tracks = board.GetTracks()

        logger.info("Showing GUI")
        dlg = Pad2PadTrackDistanceDialog(_pcbnew_frame, all_tracks, measure_distance.track_list[0][1:-1], logger)

        if user_units == 'mm':
            dlg.lbl_length.SetLabelText("%.3f" % (distance) + " mm")
            dlg.lbl_resistance.SetLabelText("%.4f" % resistance + " Ohm")
        else:
            dlg.lbl_length.SetLabelText("%.4f" % (distance/25.4) + " in")
            dlg.lbl_resistance.SetLabelText("%.4f" % resistance + " Ohm")

        dlg.Show()


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
