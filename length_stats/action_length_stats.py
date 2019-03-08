# -*- coding: utf-8 -*-
#  action_length_stats.py
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

SCALE = 1000000.0


class LenghtStatsDialog(wx.Dialog):
    def __init__(self, parent, board, netname):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Lenght stats", pos=wx.DefaultPosition, size=wx.Size(237, 384), style=wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.net_list = wx.ListCtrl(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT)
        bSizer1.Add(self.net_list, 1, wx.ALL | wx.EXPAND, 5)

        self.btn_ok = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer1.Add(self.btn_ok, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

        self.net_list.InsertColumn(0, 'Net', width=100) 
        self.net_list.InsertColumn(1, 'Length')

        for net in netname:
            index_net = netname.index(net)
            index = self.net_list.InsertStringItem(index_net, net)
            self.net_list.SetStringItem(index, 1, "0.0")

        self.board = board
        self.netname = netname

        self.timer = wx.Timer(self, 1)

        self.Bind(wx.EVT_TIMER, self.on_update, self.timer)
        self.timer.Start(500)

    def on_update(self, event):
        # get all tracks
        tracks = self.board.GetTracks()

        # find only tracks on this net
        for net in self.netname:
            tracks_on_net = []
            for t in tracks:
                if t.GetNetname() == net:
                    tracks_on_net.append(t)

            # sum their lenght
            length = 0
            for t in tracks_on_net:
                length = length + t.GetLength()/SCALE

            index_net = self.netname.index(net)
            self.net_list.SetStringItem(index_net, 1, "%.2f" % length)

        event.Skip()


class LengthStats(pcbnew.ActionPlugin):
    """
    A plugin to show track lenght of all selected nets
    How to use:
    - move to GAL
    - select track segment or pad for net you wish to find the length
    - call the plugin
    """

    def defaults(self):
        self.name = "Length stats"
        self.category = "Get tracks lenght"
        self.description = "Obtains and refreshes lenght of all tracks on selected nets"

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="length_stats.log",
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

        _pcbnew_frame = \
            filter(lambda w: w.GetTitle().lower().startswith('pcbnew'),
                   wx.GetTopLevelWindows()
                  )[0]

        # find all selected tracks and pads
        nets = set()
        selected_tracks = filter(lambda x: x.IsSelected(), board.GetTracks())

        nets.update([track.GetNetname() for track in selected_tracks])

        modules = board.GetModules()
        for mod in modules:
            pads = mod.Pads()
            nets.update([pad.GetNetname() for pad in pads if pad.IsSelected()])

        dlg = LenghtStatsDialog(_pcbnew_frame, board, list(nets))

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
