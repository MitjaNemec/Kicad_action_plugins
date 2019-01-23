# -*- coding: utf-8 -*-
#  action_replicate_layout.py
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
import replicatelayout
import os
import logging
import sys



class ReplicateLayoutDialog(wx.Dialog):
    def __init__(self, parent, replicator):

        self.replicator = replicator
        self.levels = self.replicator.get_sheet_levels()

        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Replicate layout", pos = wx.DefaultPosition, size = wx.Size( 427,521 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
        
        self.SetSizeHintsSz( wx.Size( -1,-1 ), wx.Size( -1,-1 ) )
        
        bSizer1 = wx.BoxSizer( wx.HORIZONTAL )
        
        bSizer14 = wx.BoxSizer( wx.VERTICAL )
        
        bSizer111 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Hierarchy level:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText3.Wrap( -1 )
        self.m_staticText3.SetMinSize( wx.Size( 95,-1 ) )
        
        bSizer111.Add( self.m_staticText3, 0, wx.ALL, 5 )
        
        list_levelsChoices = self.levels
        self.list_levels = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, list_levelsChoices, 0 )
        self.list_levels.SetMaxSize( wx.Size( 110,-1 ) )
        self.list_levels.SetSelection(len(self.replicator.sheet_levels)-1)
        
        bSizer111.Add( self.list_levels, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer14.Add( bSizer111, 1, wx.EXPAND, 5 )
        
        bSizer9 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.rad_btn_Linear = wx.RadioButton( self, wx.ID_ANY, u"Linear", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP )
        self.rad_btn_Linear.SetValue( True ) 
        bSizer9.Add( self.rad_btn_Linear, 0, wx.ALL, 5 )
        
        self.rad_btn_Circular = wx.RadioButton( self, wx.ID_ANY, u"Circular", wx.DefaultPosition, wx.DefaultSize )
        self.rad_btn_Circular.SetValue(False)
        bSizer9.Add( self.rad_btn_Circular, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer9, 1, wx.EXPAND, 5 )
        
        self.btn_grab_offset = wx.Button( self, wx.ID_ANY, u"Grab offset from layout", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer14.Add( self.btn_grab_offset, 0, wx.ALL, 5 )
        
        bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.lbl_x_mag = wx.StaticText( self, wx.ID_ANY, u"x offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_x_mag.Wrap( -1 )
        self.lbl_x_mag.SetMinSize( wx.Size( 95,-1 ) )
        
        bSizer2.Add( self.lbl_x_mag, 0, wx.ALL, 5 )
        
        self.val_x_mag = wx.TextCtrl( self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.val_x_mag.SetMaxSize( wx.Size( 110,-1 ) )
        
        bSizer2.Add( self.val_x_mag, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer2, 1, wx.EXPAND, 5 )
        
        bSizer3 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.lbl_y_angle = wx.StaticText( self, wx.ID_ANY, u"y offset (mm)", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_y_angle.Wrap( -1 )
        self.lbl_y_angle.SetMinSize( wx.Size( 95,-1 ) )
        
        bSizer3.Add( self.lbl_y_angle, 0, wx.ALL, 5 )
        
        self.val_y_angle = wx.TextCtrl( self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.val_y_angle.SetMaxSize( wx.Size( 110,-1 ) )
        
        bSizer3.Add( self.val_y_angle, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer3, 1, wx.EXPAND, 5 )
        
        bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.chkbox_tracks = wx.CheckBox( self, wx.ID_ANY, u"Replicate tracks", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.chkbox_tracks.SetValue(True) 
        bSizer8.Add( self.chkbox_tracks, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer8, 1, wx.EXPAND, 5 )
        
        bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.chkbox_zones = wx.CheckBox( self, wx.ID_ANY, u"Replicate zones", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.chkbox_zones.SetValue(True) 
        bSizer5.Add( self.chkbox_zones, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer5, 1, wx.EXPAND, 5 )
        
        bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.chkbox_text = wx.CheckBox( self, wx.ID_ANY, u"Replicate text", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.chkbox_text.SetValue(True) 
        bSizer6.Add( self.chkbox_text, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer6, 1, wx.EXPAND, 5 )
        
        bSizer10 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.chkbox_intersecting = wx.CheckBox( self, wx.ID_ANY, u"Replicate intersecting tracks/zones", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer10.Add( self.chkbox_intersecting, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer10, 1, wx.EXPAND, 5 )
        
        bSizer11 = wx.BoxSizer( wx.VERTICAL )
        
        self.chkbox_remove = wx.CheckBox( self, wx.ID_ANY, u"Remove existing tracks/zones", wx.DefaultPosition, wx.DefaultSize, 0 )

        bSizer11.Add( self.chkbox_remove, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer11, 1, wx.EXPAND, 5 )
        
        bSizer12 = wx.BoxSizer( wx.HORIZONTAL )
        
        self.btn_ok = wx.Button( self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.btn_ok.SetDefault() 
        bSizer12.Add( self.btn_ok, 0, wx.ALL, 5 )
        
        self.btn_cancel = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer12.Add( self.btn_cancel, 0, wx.ALL, 5 )
        
        bSizer14.Add( bSizer12, 1, wx.EXPAND, 5 )
        
        bSizer14.Add( ( 0, 0), 1, wx.EXPAND, 5 )
        
        bSizer1.Add( bSizer14, 1, wx.EXPAND, 5 )
        
        bSizer15 = wx.BoxSizer( wx.VERTICAL )
        
        self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"Sheets to replicate:", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText4.Wrap( -1 )
        bSizer15.Add( self.m_staticText4, 0, wx.ALL, 5 )
        
        index = self.list_levels.GetSelection()
        list_sheetsChoices = self.replicator.get_list_of_sheets_to_replicate(self.levels[index])
        self.list_sheets = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,195 ), list_sheetsChoices, wx.LB_MULTIPLE|wx.LB_NEEDED_SB )
        bSizer15.Add( self.list_sheets, 0, wx.ALL|wx.EXPAND, 5 )
        
        
        bSizer15.Add( ( 0, 0), 1, wx.EXPAND, 5 )
        
        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)
        
        bSizer1.Add( bSizer15, 1, wx.EXPAND, 5 )
        
        self.SetSizer( bSizer1 )
        self.Layout()
        
        self.Centre( wx.BOTH )

        # Connect Events
        self.rad_btn_Linear.Bind(wx.EVT_RADIOBUTTON, self.coordinate_system_changed)
        self.rad_btn_Circular.Bind(wx.EVT_RADIOBUTTON, self.coordinate_system_changed)

        self.btn_grab_offset.Bind(wx.EVT_BUTTON, self.grab_offest)

        self.list_levels.Bind(wx.EVT_LISTBOX, self.level_changed)

        self.minimum_radius = self.replicator.minimum_radius
        self.minimum_width = self.replicator.minimum_width
        self.minimum_angle = self.replicator.minimum_angle
        self.levels = self.replicator.get_sheet_levels()

        self.val_x_mag.SetValue("%.2f" % self.minimum_width)
        self.val_y_angle.SetValue(u"0.0")

    def level_changed(self, event):
        index = self.list_levels.GetSelection()

        self.replicator.calculate_spacing(self.levels[index])
        list_sheetsChoices = self.replicator.get_list_of_sheets_to_replicate(self.levels[index])

        # clear levels
        self.list_sheets.Clear()
        list_sheetsChoices = self.replicator.get_list_of_sheets_to_replicate(self.levels[index])
        self.list_sheets.AppendItems(list_sheetsChoices)

        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)

        self.minimum_radius = self.replicator.minimum_radius
        self.minimum_width = self.replicator.minimum_width
        self.minimum_angle = self.replicator.minimum_angle

        if self.rad_btn_Linear.GetValue():
            self.lbl_x_mag.SetLabelText(u"x offset (mm)")
            self.lbl_y_angle.SetLabelText(u"y offset (mm)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_width)
            self.val_y_angle.SetValue(u"0.0")
        else:
            self.lbl_x_mag.SetLabelText(u"radius (mm)")
            self.lbl_y_angle.SetLabelText(u"angle (deg)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_radius)
            self.val_y_angle.SetValue("%.2f" % self.minimum_angle)
        event.Skip()

    def coordinate_system_changed(self, event):
        # if cartesian
        if self.rad_btn_Linear.GetValue():
            self.rad_btn_Linear.SetValue(True)
            self.rad_btn_Circular.SetValue(False)
            self.lbl_x_mag.SetLabelText(u"x offset (mm)")
            self.lbl_y_angle.SetLabelText(u"y offset (mm)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_width)
            self.val_y_angle.SetValue(u"0.0")
        else:
            self.rad_btn_Linear.SetValue(False)
            self.rad_btn_Circular.SetValue(True)
            self.lbl_x_mag.SetLabelText(u"radius (mm)")
            self.lbl_y_angle.SetLabelText(u"angle (deg)")
            self.val_x_mag.SetValue("%.2f" % self.minimum_radius)
            self.val_y_angle.SetValue("%.2f" % self.minimum_angle)
        pass

    def grab_offest(self, event):
        # recalculate spacing, in order to grab pivot_module_clones
        index = self.list_levels.GetSelection()
        self.replicator.calculate_spacing(self.levels[index])
        offset_x, offset_y = self.replicator.estimate_offset()
        self.val_x_mag.SetValue("%.2f" % offset_x)
        self.val_y_angle.SetValue("%.2f" % offset_y)


class ReplicateLayout(pcbnew.ActionPlugin):
    """
    A script to replicate layout
    How to use:
    - move to GAL
    - select module of layout to replicate
    - call the plugin
    - enter pivot step and confirm pivod module
    """

    def defaults(self):
        self.name = "Replicate layout"
        self.category = "Modify Drawing PCB"
        self.description = "Replicate layout of a hierchical sheet"

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="replicate_layout.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S',
                            disable_existing_loggers=False)
        logger = logging.getLogger(__name__)
        logger.info("Action plugin Replicate layout started")

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

        # check if there is exactly one module selected
        selected_modules = filter(lambda x: x.IsSelected(), pcbnew.GetBoard().GetModules())
        selected_names = []
        for mod in selected_modules:
            selected_names.append("{}".format(mod.GetReference()))

        # if more or less than one show only a messagebox
        if len(selected_names) != 1:
            caption = 'Replicate Layout'
            message = "More or less than 1 module selected. Please select exactly one module and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        # if exactly one module is selected
        else:
            # this is a pivot module
            pivot_module_reference = selected_names[0]

            # prepare the replicator
            logger.info("Preparing replicator with " + pivot_module_reference + " as a reference")
            try:
                replicator = replicatelayout.Replicator(pcbnew.GetBoard(), pivot_module_reference)
            except ValueError:
                caption = 'Replicate Layout'
                message = "Selected module is on root page of schematics hierarchy!"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return

            sheet_levels = replicator.get_sheet_levels()
            logger.debug("Calculating initial spacing")
            replicator.calculate_spacing(sheet_levels[-1])

            # show dialog
            logger.debug("Showing dialog")
            x_offset = None
            y_offset = None
            dlg = ReplicateLayoutDialog(_pcbnew_frame, replicator)
            res = dlg.ShowModal()

            if res == wx.ID_OK:

                selected_items = dlg.list_sheets.GetSelections()
                slected_names = []
                for sel in selected_items:
                    slected_names.append(dlg.list_sheets.GetString(sel))

                try:
                    x_offset = float(dlg.val_x_mag.GetValue())
                except:
                    x_offset = None
                try:
                    y_offset = float(dlg.val_y_angle.GetValue())
                except:
                    y_offset = None
                replicate_containing_only = not dlg.chkbox_intersecting.GetValue()
                remove_existing_nets_zones = dlg.chkbox_remove.GetValue()
                rep_tracks = dlg.chkbox_tracks.GetValue()
                rep_zones = dlg.chkbox_zones.GetValue()
                rep_text = dlg.chkbox_text.GetValue()
                polar = dlg.rad_btn_Circular.GetValue()
            else:
                return

            # execute replicate_layout
            if (x_offset is None) or (y_offset is None):
                logger.info("error parsing x offset and/or y offset input values")
                caption = 'Replicate Layout'
                message = "error parsing x offset and/or y offset input values"
                dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                # failsafe somtimes on my machine wx does not generate a listbox event
                index = dlg.list_levels.GetSelection()
                replicator.calculate_spacing(dlg.levels[index])

                # replicate now
                logger.info("Replicating layout")
                replicator.replicate_layout(x_offset, y_offset,
                                            replicate_containing_only,
                                            remove_existing_nets_zones,
                                            rep_tracks,
                                            rep_zones, rep_text,
                                            polar)
                logger.info("Replication complete")
                pcbnew.Refresh()


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
