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
import place_footprints
import os
import logging
import sys
import math
import re


def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)


class PlaceBySheet (wx.Dialog):

    # Virtual event handlers, overide them in your derived class
    def level_changed(self, event):
        index = self.list_levels.GetSelection()

        self.list_sheetsChoices = self.placer.get_sheets_to_replicate(self.pivot_mod, self.pivot_mod.sheet_id[index])

        list = [('/').join(x) for x in self.list_sheetsChoices]
        # clear levels
        self.list_sheets.Clear()
        self.list_sheets.AppendItems(list)

        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)
        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)

        if self.rad_btn_linear_sheet.GetValue() or self.rad_btn_matrix_sheet.GetValue():
            self.lbl_x_mag.SetLabelText(u"step x (mm):")
            self.lbl_y_angle.SetLabelText(u"step y (mm):")
            self.val_x_mag.SetValue("%.2f" % self.width)
            self.val_y_angle.SetValue("%.2f" % self.height)
        # circular layout
        else:
            number_of_all_sheets = len(self.list_sheets.GetSelections())
            circumference = number_of_all_sheets * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / number_of_all_sheets
            self.lbl_x_mag.SetLabelText(u"radius (mm):")
            self.lbl_y_angle.SetLabelText(u"angle (deg):")
            self.val_x_mag.SetValue("%.2f" % radius)
            self.val_y_angle.SetValue("%.2f" % angle)

    def arrangement_changed(self, event):

        if self.rad_btn_linear_sheet.GetValue() or self.rad_btn_matrix_sheet.GetValue():
            self.lbl_x_mag.SetLabelText(u"step x (mm):")
            self.lbl_y_angle.SetLabelText(u"step y (mm):")
            self.val_x_mag.SetValue("%.2f" % self.width)
            self.val_y_angle.SetValue("%.2f" % self.height)
        # circular layout
        else:
            number_of_all_sheets = len(self.list_sheets.GetSelections())
            circumference = number_of_all_sheets * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / number_of_all_sheets
            self.lbl_x_mag.SetLabelText(u"radius (mm):")
            self.lbl_y_angle.SetLabelText(u"angle (deg):")
            self.val_x_mag.SetValue("%.2f" % radius)
            self.val_y_angle.SetValue("%.2f" % angle)

    def __init__(self, parent, placer, pivot_mod):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Place footprints", pos=wx.DefaultPosition, size=wx.Size(258, 492), style=wx.DEFAULT_DIALOG_STYLE)

        # self.SetSizeHintsSz( wx.Size( 258,409 ), wx.DefaultSize )

        bSizer14 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText5 = wx.StaticText(self, wx.ID_ANY, u"Hierarchy level:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText5.Wrap(-1)
        bSizer14.Add(self.m_staticText5, 0, wx.ALL, 5)

        bSizer18 = wx.BoxSizer(wx.HORIZONTAL)

        list_levelsChoices = []
        self.list_levels = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(230, -1), list_levelsChoices, 0)
        bSizer18.Add(self.list_levels, 1, wx.ALL | wx.EXPAND, 5)

        bSizer14.Add(bSizer18, 1, wx.EXPAND, 5)

        self.m_staticText6 = wx.StaticText(self, wx.ID_ANY, u"Sheets to replicate:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText6.Wrap(-1)
        bSizer14.Add(self.m_staticText6, 0, wx.ALL, 5)

        bSizer16 = wx.BoxSizer(wx.HORIZONTAL)

        self.list_sheetsChoices = []
        self.list_sheets = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.Size(230, -1), self.list_sheetsChoices, wx.LB_MULTIPLE | wx.LB_NEEDED_SB)
        bSizer16.Add(self.list_sheets, 1, wx.ALL | wx.EXPAND, 5)

        bSizer14.Add(bSizer16, 2, wx.EXPAND, 5)

        self.m_staticline2 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        bSizer14.Add(self.m_staticline2, 0, wx.EXPAND | wx.ALL, 5)

        self.m_staticText3 = wx.StaticText(self, wx.ID_ANY, u"Arrangement:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText3.Wrap(-1)
        bSizer14.Add(self.m_staticText3, 0, wx.ALL, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.rad_btn_linear_sheet = wx.RadioButton(self, wx.ID_ANY, u"Linear", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.rad_btn_linear_sheet.SetValue(True)
        bSizer5.Add(self.rad_btn_linear_sheet, 0, wx.ALL, 5)

        self.rad_btn_matrix_sheet = wx.RadioButton(self, wx.ID_ANY, u"Matrix", wx.DefaultPosition, wx.DefaultSize)
        bSizer5.Add(self.rad_btn_matrix_sheet, 0, wx.ALL, 5)

        self.rad_btn_circular_sheet = wx.RadioButton(self, wx.ID_ANY, u"Circular", wx.DefaultPosition, wx.DefaultSize)
        bSizer5.Add(self.rad_btn_circular_sheet, 0, wx.ALL, 5)

        bSizer14.Add(bSizer5, 0, wx.EXPAND, 5)

        self.m_staticline1 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        bSizer14.Add(self.m_staticline1, 0, wx.EXPAND | wx.ALL, 5)

        bSizer6 = wx.BoxSizer(wx.HORIZONTAL)

        gSizer1 = wx.GridSizer(0, 2, 0, 0)

        self.lbl_x_mag = wx.StaticText(self, wx.ID_ANY, u"step x (mm):", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.lbl_x_mag.Wrap(-1)
        gSizer1.Add( self.lbl_x_mag, 0, wx.ALL, 5)

        self.val_x_mag = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.val_x_mag, 0, wx.ALL, 5)

        self.lbl_y_angle = wx.StaticText(self, wx.ID_ANY, u"step y (mm):", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_y_angle.Wrap(-1)
        gSizer1.Add(self.lbl_y_angle, 0, wx.ALL, 5)

        self.val_y_angle = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.val_y_angle, 0, wx.ALL, 5)

        self.btn_ok = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.btn_ok, 0, wx.ALL, 5)

        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.btn_cancel, 0, wx.ALL, 5)

        bSizer6.Add(gSizer1, 0, wx.EXPAND, 5)

        bSizer14.Add(bSizer6, 0, wx.EXPAND, 5)

        self.SetSizer(bSizer14)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.list_levels.Bind(wx.EVT_LISTBOX, self.level_changed)

        self.rad_btn_circular_sheet.Bind(wx.EVT_RADIOBUTTON, self.arrangement_changed)
        self.rad_btn_linear_sheet.Bind(wx.EVT_RADIOBUTTON, self.arrangement_changed)
        self.rad_btn_matrix_sheet.Bind(wx.EVT_RADIOBUTTON, self.arrangement_changed)

        self.placer = placer
        self.pivot_mod = self.placer.get_mod_by_ref(pivot_mod)

        modules = self.placer.get_modules_on_sheet(self.pivot_mod.sheet_id)
        self.height, self.width = self.placer.get_modules_bounding_box(modules)


class PlaceByReference (wx.Dialog):

    # Virtual event handlers, overide them in your derived class
    def ar_ch(self, event):
        if self.rad_btn_linear_ref.GetValue() or self.rad_btn_matrix_ref.GetValue():
            self.lbl_x_mag.SetLabelText(u"step x (mm):")
            self.lbl_y_angle.SetLabelText(u"step y (mm):")
            self.val_x_mag.SetValue("%.2f" % self.width)
            self.val_y_angle.SetValue("%.2f" % self.height)
        # circular layout
        else:
            number_of_all_modules = len(self.list_modules.GetSelections())
            circumference = number_of_all_modules * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / number_of_all_modules
            self.lbl_x_mag.SetLabelText(u"radius (mm):")
            self.lbl_y_angle.SetLabelText(u"angle (deg):")
            self.val_x_mag.SetValue("%.2f" % radius)
            self.val_y_angle.SetValue("%.2f" % angle)

        event.Skip()

    def __init__(self, parent, placer, pivot_mod):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Place footprints", pos=wx.DefaultPosition, size=wx.Size(260, 496), style=wx.DEFAULT_DIALOG_STYLE)

        # self.SetSizeHintsSz( wx.Size( 257,-1 ), wx.DefaultSize )

        bSizer3 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText2 = wx.StaticText(self, wx.ID_ANY, u"List of footprints:", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText2.Wrap(-1)
        bSizer3.Add(self.m_staticText2, 0, wx.ALL, 5)

        list_modulesChoices = []
        self.list_modules = wx.ListBox(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, list_modulesChoices, wx.LB_MULTIPLE | wx.LB_NEEDED_SB)
        bSizer3.Add(self.list_modules, 1, wx.ALL | wx.EXPAND, 5)

        self.m_staticline1 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        bSizer3.Add(self.m_staticline1, 0, wx.EXPAND | wx.ALL, 5)

        self.m_staticText3 = wx.StaticText(self, wx.ID_ANY, u"Arrangement", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText3.Wrap(-1)
        bSizer3.Add(self.m_staticText3, 0, wx.ALL, 5)

        bSizer5 = wx.BoxSizer(wx.HORIZONTAL)

        self.rad_btn_linear_ref = wx.RadioButton(self, wx.ID_ANY, u"Linear", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.rad_btn_linear_ref.SetValue(True)
        bSizer5.Add(self.rad_btn_linear_ref, 0, wx.ALL, 5)

        self.rad_btn_matrix_ref = wx.RadioButton(self, wx.ID_ANY, u"Matrix", wx.DefaultPosition, wx.DefaultSize)
        bSizer5.Add(self.rad_btn_matrix_ref, 0, wx.ALL, 5)

        self.rad_btn_circular_ref = wx.RadioButton(self, wx.ID_ANY, u"Circular", wx.DefaultPosition, wx.DefaultSize)
        bSizer5.Add(self.rad_btn_circular_ref, 0, wx.ALL, 5)

        bSizer3.Add(bSizer5, 0, wx.EXPAND, 5)

        self.m_staticline2 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        bSizer3.Add(self.m_staticline2, 0, wx.EXPAND | wx.ALL, 5)

        bSizer14 = wx.BoxSizer(wx.HORIZONTAL)

        bSizer3.Add(bSizer14, 0, wx.EXPAND, 5)

        bSizer17 = wx.BoxSizer(wx.HORIZONTAL)

        gSizer1 = wx.GridSizer(3, 2, 0, 0)

        self.lbl_x_mag = wx.StaticText(self, wx.ID_ANY, u"step x (mm):", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_x_mag.Wrap(-1)
        gSizer1.Add(self.lbl_x_mag, 0, wx.ALL, 5)

        self.val_x_mag = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.val_x_mag, 0, wx.ALL, 5)

        self.lbl_y_angle = wx.StaticText(self, wx.ID_ANY, u"step y (mm):", wx.DefaultPosition, wx.DefaultSize, 0)
        self.lbl_y_angle.Wrap(-1)
        gSizer1.Add(self.lbl_y_angle, 0, wx.ALL, 5)

        self.val_y_angle = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.val_y_angle, 1, wx.ALL, 5)

        self.btn_ok = wx.Button(self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.btn_ok, 0, wx.ALL, 5)

        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0)
        gSizer1.Add(self.btn_cancel, 0, wx.ALL, 5)

        bSizer17.Add(gSizer1, 0, wx.EXPAND, 5)

        bSizer3.Add(bSizer17, 0, wx.EXPAND, 5)

        self.SetSizer(bSizer3)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.rad_btn_linear_ref.Bind(wx.EVT_RADIOBUTTON, self.ar_ch)
        self.rad_btn_circular_ref.Bind(wx.EVT_RADIOBUTTON, self.ar_ch)
        self.rad_btn_matrix_ref.Bind(wx.EVT_RADIOBUTTON, self.ar_ch)

        self.placer = placer
        self.pivot_mod = self.placer.get_mod_by_ref(pivot_mod)

        self.height, self.width = self.placer.get_modules_bounding_box([self.pivot_mod])

        self.val_x_mag.SetValue("%.2f" % self.width)
        self.val_y_angle.SetValue("%.2f" % self.height)


class InitialDialog (wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=u"Place footprints", pos=wx.DefaultPosition, size=wx.Size(242, 107), style=wx.DEFAULT_DIALOG_STYLE)

        # self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.m_staticText1 = wx.StaticText(self, wx.ID_ANY, u"Place by?", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText1.Wrap(-1)
        bSizer1.Add( self.m_staticText1, 0, wx.ALL, 5)

        bSizer2 = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_reference = wx.Button(self, wx.ID_OK, u"Reference nr.", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.btn_reference, 0, wx.ALL, 5)

        self.btn_sheet = wx.Button(self, wx.ID_CANCEL, u"Sheet nr.", wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer2.Add(self.btn_sheet, 0, wx.ALL, 5)

        bSizer1.Add(bSizer2, 1, wx.EXPAND, 5)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)


class PlaceFootprints(pcbnew.ActionPlugin):
    """
    A script to replicate layout
    How to use:
    - move to GAL
    - select module of layout to replicate
    - call the plugin
    - enter pivot step and confirm pivod module
    """

    def defaults(self):
        self.name = "Place footprints"
        self.category = "Modify Drawing PCB"
        self.description = "Place footprints along a predefined pattern (line, matrix, circle)"

    def Run(self):
        # load board
        board = pcbnew.GetBoard()

        # go to the project folder - so that log will be in proper place
        os.chdir(os.path.dirname(os.path.abspath(board.GetFileName())))

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="place_footprints.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S',
                            disable_existing_loggers=False)
        logger = logging.getLogger(__name__)
        logger.info("Action plugin Place footprints started")

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
            caption = 'Place footprints'
            message = "More or less than 1 module selected. Please select exactly one module and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # this it the reference footprint
        pivot_module_reference = selected_names[0]

        # ask user which way to select other footprints (by increasing reference number or by ID
        dlg = InitialDialog(_pcbnew_frame)
        res = dlg.ShowModal()

        placer = place_footprints.Placer(board)

        pivot_module = placer.get_mod_by_ref(pivot_module_reference)

        # by reference number
        if res == wx.ID_OK:
            # get list of all subsequent modules
            module_reference_designator = ''.join(i for i in pivot_module_reference if not i.isdigit())
            module_reference_number = int(''.join(i for i in pivot_module_reference if i.isdigit()))

            # get list of all modules with same reference designator
            list_of_all_modules_with_same_designaro = placer.get_modules_with_reference_designator(module_reference_designator)
            list_of_all_modules_with_same_designaro.sort()

            list_of_consecutive_modules=[]
            start_index = list_of_all_modules_with_same_designaro.index(pivot_module_reference)
            count_start = module_reference_number
            for mod in list_of_all_modules_with_same_designaro[start_index:]:
                if int(''.join(i for i in pivot_module_reference if i.isdigit())) == count_start:
                    count_start = count_start + 1
                    list_of_consecutive_modules.append(mod)
                else:
                    break
            
            count_start = module_reference_number
            for x in reversed(list_of_all_modules_with_same_designaro[:start_index]):
                if int(''.join(i for i in pivot_module_reference if i.isdigit())) == count_start:
                    count_start = count_start -1
                    list_of_consecutive_modules.append(mod)
                else:
                    break

            # display dialog
            dlg = PlaceByReference(_pcbnew_frame, placer, pivot_module_reference)
            dlg.list_modules.AppendItems(list_of_consecutive_modules)
            res = dlg.ShowModal()

            # get list of modules to place
            modules_to_place_indeces = dlg.list_modules.GetSelections()
            modules_to_place = [list_of_consecutive_modules[i] for i in modules_to_place_indeces]
            # get mode
            if dlg.rad_btn_circular_ref.GetValue():
                delta_angle = float(dlg.val_y_angle.GetValue())
                radius = float(dlg.val_x_mag.GetValue())
                placer.place_circular(modules_to_place, radius, delta_angle)

            if dlg.rad_btn_linear_ref.GetValue():
                step_x = float(dlg.val_x_mag.GetValue())
                step_y = float(dlg.val_y_angle.GetValue())
                placer.place_linear(modules_to_place, step_x, step_y)

            if dlg.rad_btn_matrix_ref.GetValue():
                step_x = float(dlg.val_x_mag.GetValue())
                step_y = float(dlg.val_y_angle.GetValue())
                placer.place_matrix(modules_to_place, step_x, step_y)

        # by sheet
        else:
            # get list of all modules with same ID
            list_of_modules = placer.get_list_of_modules_with_same_id(pivot_module.mod_id)
            # display dialog
            dlg = PlaceBySheet(_pcbnew_frame, placer, pivot_module_reference)
            levels = pivot_module.filename
            dlg.list_levels.Clear()
            dlg.list_levels.AppendItems(levels)
            res = dlg.ShowModal()

            # based on the sheet list, find all the modules with same ID
            sheets_to_place_indeces = dlg.list_sheets.GetSelections()
            sheets_to_place = [dlg.list_sheetsChoices[i] for i in sheets_to_place_indeces]

            mod_references = [pivot_module_reference]
            for mod in list_of_modules:
                if mod.sheet_id in sheets_to_place:
                    mod_references.append(mod.ref)

            # sort by reference number
            sorted_modules = natural_sort(mod_references)

            # get mode
            if dlg.rad_btn_circular_sheet.GetValue():
                delta_angle = float(dlg.val_y_angle.GetValue())
                radius = float(dlg.val_x_mag.GetValue())
                placer.place_circular(mod_references, radius, delta_angle)

            if dlg.rad_btn_linear_sheet.GetValue():
                step_x = float(dlg.val_x_mag.GetValue())
                step_y = float(dlg.val_y_angle.GetValue())
                placer.place_linear(mod_references, step_x, step_y)

            if dlg.rad_btn_matrix_sheet.GetValue():
                step_x = float(dlg.val_x_mag.GetValue())
                step_y = float(dlg.val_y_angle.GetValue())
                placer.place_matrix(mod_references, step_x, step_y)

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
