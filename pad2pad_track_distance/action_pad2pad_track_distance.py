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
else:
    from . import pad2pad_track_distance

SCALE = 1000000.0


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

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="pad2pad_track_distance.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S',
                            disable_existing_loggers=False)
        logger = logging.getLogger(__name__)
        logger.info("Action plugin Length stats started")

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
            module_pads = mod.PadsList()
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
            return

        # and if they are on different nest
        if nets[0] != nets[1]:
            caption = 'Pad2Pad Track Distance'
            message = "The selected pads are not on the same net"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
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
            return
        except Exception:
            logger.exception("Fatal error when measuring")
            raise

        # trying to show in layout which tracks are taken into account - so far it does not work
        # as the selection is automatically cleared when exiting action plugin
        # I'll leave this code in just for reference
        selected_pads[0].ClearSelected()
        selected_pads[1].ClearSelected()

        # deselect all tracks except used ones
        all_tracks = board.GetTracks()

        for track in all_tracks:
            if track not in measure_distance.track_list:
                track.ClearSelected()
            else:
                track.SetSelected()
                track.SetBrightened()
                track.SetHighlighted()

        # zoom the layout window to show the tracks taken into account
        pad1_pos = selected_pads[0].GetPosition()
        pad2_pos = selected_pads[1].GetPosition()
        if pad1_pos[0] > pad2_pos[0]:
            x = pad2_pos[0]
            width = pad1_pos[0] - pad2_pos[0]
        else:
            x = pad1_pos[0]
            width = pad2_pos[0] - pad1_pos[0]

        if pad1_pos[1] > pad2_pos[1]:
            y = pad2_pos[1]
            height = pad1_pos[1] - pad2_pos[1]
        else:
            y = pad1_pos[1]
            height = pad2_pos[1] - pad1_pos[1]

        pcbnew.WindowZoom(x, y, width, height)
        # pcbnew.Refresh()

        caption = 'Pad2Pad Track Distance'
        if user_units == 'mm':
            message = "Distance between pads is " + "%.3f" % (distance) + " mm" \
                    + "\nResistance between pads is " + "%.4f" % resistance + " Ohm"
        else:
            message = "Distance between pads is " + "%.4f" % (distance/25.4) + " in" \
                    + "\nResistance between pads is " + "%.4f" % resistance + " Ohm"
        dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

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

