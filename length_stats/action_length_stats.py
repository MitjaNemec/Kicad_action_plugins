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
import timeit

if __name__ == '__main__':
    import length_stats_GUI
else:
    from . import length_stats_GUI

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


class LengthStatsDialog(length_stats_GUI.LengthStatsGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(LengthStatsDialog, self).SetSizeHints(sz1, sz2)

    def __init__(self,  parent, board, nets, logger):
        length_stats_GUI.LengthStatsGUI.__init__(self, parent)

        self.net_list.InsertColumn(0, 'Net', width=100) 
        self.net_list.InsertColumn(1, 'Length')

        self.net_data = []

        nets.sort()
        #remove empty nets
        for net in nets:
            if not net:
                nets.remove(net)

        for net in nets:
            index_net = nets.index(net)
            index = self.net_list.InsertStringItem(index_net, net)
            self.net_list.SetStringItem(index, 1, "0.0")
            self.net_data.append( (net, 0.0) )

        self.board = board
        self.nets = nets
        self.logger = logger

        self.column_sorted = 0
        self.column_0_dir = 0
        self.column_1_dir = 0

        self.timer = wx.Timer(self, 1)
        self.refresh_time = 0.1

        self.sort_items(None)

        self.Bind(wx.EVT_TIMER, self.on_update, self.timer)

        self.logger.info("Length stats gui initialized")
        self.logger.info("Nets for stats are;\n" + repr(self.nets))

    def cont_refresh_toggle(self, event):
        if self.chk_cont.IsChecked():
            self.logger.info("Automatic refresh turned on")
            self.timer.Start(self.refresh_time * 10 * 1000)
        else:
            self.logger.info("Automatic refresh turned off")
            self.timer.Stop()
        event.Skip()

    def on_btn_refresh(self, event):
        self.logger.info("Refreshing manually")
        self.refresh()
        event.Skip()
		

    def on_btn_ok(self, event):
        # remove higlightning from tracks
        tracks = self.board.GetTracks()
        for track in tracks:
            track.ClearBrightened()

        pcbnew.Refresh()

        self.logger.info("Closing GUI")
        logging.shutdown()
        self.Close()
        event.Skip()

    def on_update(self, event):
        self.logger.info("Autimatic refresh")
        self.refresh()
        event.Skip()

    def refresh(self):
        self.logger.info("Refreshing net lengths")
        start_time = timeit.default_timer()

        # go through all the nets
        for net in self.nets:
            # get tracks on net
            netcode = self.board.GetNetcodeFromNetname(net)
            tracks_on_net = self.board.TracksInNet(netcode)

            # sum their length
            length = 0
            for t in tracks_on_net:
                length = length + t.GetLength()/SCALE

            index_net = self.nets.index(net)
            self.net_data[index_net] = (net, length)
            self.net_list.SetStringItem(index_net, 1, "%.2f" % length)

        stop_time = timeit.default_timer()
        delta_time = stop_time - start_time
        if delta_time > 0.05:
            self.refresh_time = delta_time
        else:
            self.refresh_time = 0.05
        self.lbl_refresh_time.SetLabelText(u"Refresh time: %.2f s" % delta_time)

    def delete_items(self, event):
        self.logger.info("Deleting nets")
        # test if delete key was pressed
        if event.GetKeyCode() == wx.WXK_DELETE:
            # find selected items
            selected_items = []
            for index in range(self.net_list.GetItemCount()):
                if self.net_list.IsSelected(index):
                    selected_items.append( (index, self.nets[index]))

            selected_items.sort(key=lambda tup: tup[0], reverse=True)

            # remove selected items from the back
            for item in selected_items:
                self.net_list.DeleteItem(item[0])
                del self.nets[item[0]]
                del self.net_data[item[0]]

        event.Skip()

    def item_selected(self, event):
        tracks = self.board.GetTracks()
        # get all tracks which we are interested in
        list_tracks = []
        for track in tracks:
            if track.GetNetname() in self.nets:
                list_tracks.append(track)

        # remove highlight on all tracks
        self.logger.info("Removing highlights for nets:\n" + repr(self.nets))
        for track in list_tracks:
            track.ClearBrightened()

        pcbnew.Refresh()
        # find selected tracks
        selected_items = []
        for index in range(self.net_list.GetItemCount()):
            if self.net_list.IsSelected(index):
                selected_items.append(self.nets[index])        

        self.logger.info("Adding highlights for nets:\n" + repr(selected_items))
        for track in list_tracks:
            if track.GetNetname() in selected_items:
                track.SetBrightened()

        pcbnew.Refresh()
        event.Skip()

    def sort_items(self, event):
        self.logger.info("Sorting list")
        # find which columnt to sort
        if event:
            self.column_sorted = event.m_col
        else:
            self.column_sorted = 0

        # sort column 0
        if self.column_sorted == 0:
            # ascending
            if self.column_0_dir == 0:
                self.column_0_dir = 1
                self.net_data.sort(key=lambda tup: tup[0], reverse=True)
            # descending
            else:
                self.column_0_dir = 0
                self.net_data.sort(key=lambda tup: tup[0], reverse=False)
        # sort column 1
        else:
            # ascending
            if self.column_1_dir == 0:
                self.column_1_dir = 1
                self.net_data.sort(key=lambda tup: tup[1], reverse=True)
            # descending
            else:
                self.column_1_dir = 0
                self.net_data.sort(key=lambda tup: tup[1], reverse=False)
                # sort

        self.nets = [x[0] for x in self.net_data]

        # clear and repopulate the list ctrl
        self.net_list.DeleteAllItems()
        for net in self.net_data:
            index_net = self.net_data.index(net)
            index = self.net_list.InsertStringItem(index_net, net[0])
            self.net_list.SetStringItem(index, 1, "%.2f" % net[1])

        if event:
            event.Skip()


    def copy_items(self, event):
        self.logger.info("Copying List")
        selectedItems = []
        row = []
        for j in xrange(self.net_list.GetColumnCount()):
            row.append(self.net_list.GetColumn(j).GetText())
        selectedItems.append("\t".join(row))
        for i in xrange(self.net_list.GetItemCount()):
            row = []
            for j in xrange(self.net_list.GetColumnCount()):
                row.append(self.net_list.GetItemText(i,j))
            selectedItems.append("\t".join(row))

        clipdata = wx.TextDataObject()
        clipdata.SetText("\n".join(selectedItems))
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()
        event.Skip()


class LengthStats(pcbnew.ActionPlugin):
    """
    A plugin to show track length of all selected nets
    How to use:
    - move to GAL
    - select track segment or pad for net you wish to find the length
    - call the plugin
    """

    def defaults(self):
        self.name = "Length stats"
        self.category = "Get tracks length"
        self.description = "Obtains and refreshes length of all tracks on selected nets"
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'ps_diff_pair_tune_length-length_stats.svg.png')
                
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
                            filename="length_stats.log",
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

        # find all selected tracks and pads
        nets = set()
        selected_tracks = [x for x in board.GetTracks() if x.IsSelected()]

        nets.update([track.GetNetname() for track in selected_tracks])

        modules = board.GetModules()
        for mod in modules:
            pads = mod.Pads()
            nets.update([pad.GetNetname() for pad in pads if pad.IsSelected()])

        dlg = LengthStatsDialog(_pcbnew_frame, board, list(nets), logger)
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
