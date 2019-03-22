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

import initial_dialog_GUI
import place_by_reference_GUI
import place_by_sheet_GUI

def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)


class PlaceBySheet(place_by_sheet_GUI.PlaceBySheetGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(InitialDialog, self).SetSizeHints(sz1, sz2)

    # Virtual event handlers, overide them in your derived class
    def level_changed(self, event):
        index = self.list_levels.GetSelection()

        self.list_sheetsChoices = self.placer.get_sheets_to_replicate(self.pivot_mod, self.pivot_mod.sheet_id[index])

        # get anchor modules
        anchor_modules = self.placer.get_list_of_modules_with_same_id(self.pivot_mod.mod_id)
        # find matching anchors to maching sheets
        ref_list = []
        for sheet in self.list_sheetsChoices:
            for mod in anchor_modules:
                if "/".join(sheet) in "/".join(mod.sheet_id):
                    ref_list.append(mod.ref)
                    break

        sheets_for_list = [('/').join(x[0]) + " (" + x[1] + ")" for x in zip(self.list_sheetsChoices, ref_list)]
        # clear levels
        self.list_sheets.Clear()
        self.list_sheets.AppendItems(sheets_for_list)

        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)

        if self.com_arr.GetStringSelection() == u"Linear":
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"step x (mm):")
                self.lbl_y_angle.SetLabelText(u"step y (mm):")
                self.val_x_mag.SetValue("%.3f" % self.width)
                self.val_y_angle.SetValue("%.3f" % self.height)
            else:
                self.lbl_x_mag.SetLabelText(u"step x (in):")
                self.lbl_y_angle.SetLabelText(u"step y (in):")
                self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
                self.val_y_angle.SetValue("%.3f" % (self.height/25.4))
            self.lbl_columns.Hide()
            self.val_columns.Hide()
        if self.com_arr.GetStringSelection() == u"Matrix":
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"step x (mm):")
                self.lbl_y_angle.SetLabelText(u"step y (mm):")
                self.val_x_mag.SetValue("%.3f" % self.width)
                self.val_y_angle.SetValue("%.3f" % self.height)
            else:
                self.lbl_x_mag.SetLabelText(u"step x (in):")
                self.lbl_y_angle.SetLabelText(u"step y (in):")
                self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
                self.val_y_angle.SetValue("%.3f" % (self.height/25.4))
            self.lbl_columns.Show()
            self.val_columns.Show()
        # circular layout
        if self.com_arr.GetStringSelection() == u"Circular":
            number_of_all_sheets = len(self.list_sheets.GetSelections())
            circumference = number_of_all_sheets * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / number_of_all_sheets
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"radius (mm):")
                self.val_x_mag.SetValue("%.3f" % radius)
            else:
                self.lbl_x_mag.SetLabelText(u"radius (in):")
                self.val_x_mag.SetValue("%.3f" % (radius/25.4))
            self.lbl_y_angle.SetLabelText(u"angle (deg):")
            self.val_y_angle.SetValue("%.3f" % angle)
            self.lbl_columns.Hide()
            self.val_columns.Hide()

    def arr_changed(self, event):
        if self.com_arr.GetStringSelection() == u"Linear":
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"step x (mm):")
                self.lbl_y_angle.SetLabelText(u"step y (mm):")
                self.val_x_mag.SetValue("%.3f" % self.width)
                self.val_y_angle.SetValue("%.3f" % self.height)
            else:
                self.lbl_x_mag.SetLabelText(u"step x (in):")
                self.lbl_y_angle.SetLabelText(u"step y (in):")
                self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
                self.val_y_angle.SetValue("%.3f" % (self.height/25.4))
            self.lbl_columns.Hide()
            self.val_columns.Hide()
        if self.com_arr.GetStringSelection() == u"Matrix":
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"step x (mm):")
                self.lbl_y_angle.SetLabelText(u"step y (mm):")
                self.val_x_mag.SetValue("%.3f" % self.width)
                self.val_y_angle.SetValue("%.3f" % self.height)
            else:
                self.lbl_x_mag.SetLabelText(u"step x (in):")
                self.lbl_y_angle.SetLabelText(u"step y (in):")
                self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
                self.val_y_angle.SetValue("%.3f" % (self.height/25.4))
            self.lbl_columns.Show()
            self.val_columns.Show()
        # circular layout
        if self.com_arr.GetStringSelection() == u"Circular":
            number_of_all_sheets = len(self.list_sheets.GetSelections())
            circumference = number_of_all_sheets * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / number_of_all_sheets
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"radius (mm):")
                self.val_x_mag.SetValue("%.3f" % radius)
            else:
                self.lbl_x_mag.SetLabelText(u"radius (in):")
                self.val_x_mag.SetValue("%.3f" % (radius/25.4))
            self.lbl_y_angle.SetLabelText(u"angle (deg):")
            self.val_y_angle.SetValue("%.3f" % angle)
            self.lbl_columns.Hide()
            self.val_columns.Hide()
        event.Skip()

    def __init__(self, parent, placer, pivot_mod, user_units):
        place_by_sheet_GUI.PlaceBySheetGUI.__init__(self, parent)

        if user_units == 'mm':
            self.lbl_x_mag.SetLabelText(u"step x (mm):")
        else:
            self.lbl_x_mag.SetLabelText(u"step x (in):")

        if user_units == 'mm':
            self.lbl_y_angle.SetLabelText(u"step y (mm):")
        else:
            self.lbl_y_angle.SetLabelText(u"step y (in):")

        # Connect Events
        self.list_levels.Bind(wx.EVT_LISTBOX, self.level_changed)
        self.com_arr.Bind(wx.EVT_COMBOBOX, self.arr_changed)

        self.placer = placer
        self.user_units = user_units
        self.pivot_mod = self.placer.get_mod_by_ref(pivot_mod)

        modules = self.placer.get_modules_on_sheet(self.pivot_mod.sheet_id)
        self.height, self.width = self.placer.get_modules_bounding_box(modules)


class PlaceByReference(place_by_reference_GUI.PlaceByReferenceGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(InitialDialog, self).SetSizeHints(sz1, sz2)

    # Virtual event handlers, overide them in your derived class
    def arr_changed(self, event):
        # linear layout
        if self.com_arr.GetStringSelection() == u"Linear":
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"step x (mm):")
                self.lbl_y_angle.SetLabelText(u"step y (mm):")
                self.val_x_mag.SetValue("%.3f" % self.width)
                self.val_y_angle.SetValue("%.3f" % self.height)
            else:
                self.lbl_x_mag.SetLabelText(u"step x (in):")
                self.lbl_y_angle.SetLabelText(u"step y (in):")
                self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
                self.val_y_angle.SetValue("%.3f" % (self.height/25.4))
            self.lbl_columns.Hide()
            self.val_columns.Hide()
        #Matrix
        if self.com_arr.GetStringSelection() == u"Matrix":
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"step x (mm):")
                self.lbl_y_angle.SetLabelText(u"step y (mm):")
                self.val_x_mag.SetValue("%.3f" % self.width)
                self.val_y_angle.SetValue("%.3f" % self.height)
            else:
                self.lbl_x_mag.SetLabelText(u"step x (in):")
                self.lbl_y_angle.SetLabelText(u"step y (in):")
                self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
                self.val_y_angle.SetValue("%.3f" % (self.height/25.4))
            self.lbl_columns.Show()
            self.val_columns.Show()
        # circular layout
        if self.com_arr.GetStringSelection() == u"Circular":
            number_of_all_modules = len(self.list_modules.GetSelections())
            circumference = number_of_all_modules * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / number_of_all_modules
            if self.user_units == 'mm':
                self.lbl_x_mag.SetLabelText(u"radius (mm):")
                self.val_x_mag.SetValue("%.3f" % radius)
            else:
                self.lbl_x_mag.SetLabelText(u"radius (in):")
                self.val_x_mag.SetValue("%.3f" % (radius/25.4))
            self.lbl_y_angle.SetLabelText(u"angle (deg):")
            self.val_y_angle.SetValue("%.3f" % angle)
            self.lbl_columns.Hide()
            self.val_columns.Hide()
        event.Skip()

    def __init__(self, parent, placer, pivot_mod, user_units):
        place_by_reference_GUI.PlaceByReferenceGUI.__init__(self, parent)

        if user_units == 'mm':
            self.lbl_x_mag.SetLabelText(u"step x (mm):")
        else:
            self.lbl_x_mag.SetLabelText(u"step x (in):")

        if user_units == 'mm':
            self.lbl_y_angle.SetLabelText(u"step y (mm):")
        else:
            self.lbl_y_angle.SetLabelText(u"step y (in):")

        # Connect Events
        self.com_arr.Bind(wx.EVT_COMBOBOX, self.arr_changed)

        self.placer = placer
        self.user_units = user_units
        self.pivot_mod = self.placer.get_mod_by_ref(pivot_mod)

        self.height, self.width = self.placer.get_modules_bounding_box([self.pivot_mod])

        if user_units == 'mm':
            self.val_x_mag.SetValue("%.3f" % self.width)
            self.val_y_angle.SetValue("%.3f" % self.height)
        else:
            self.val_x_mag.SetValue("%.3f" % (self.width/25.4))
            self.val_y_angle.SetValue("%.3f" % (self.height/25.4))


class InitialDialog(initial_dialog_GUI.InitialDialogGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        try:
            # wxPython 3
            self.SetSizeHintsSz(sz1, sz2)
        except TypeError:
            # wxPython 4
            super(InitialDialog, self).SetSizeHints(sz1, sz2)

    def __init__(self, parent):
        initial_dialog_GUI.InitialDialogGUI.__init__(self, parent)


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
        self.icon_file_name = os.path.join(
                os.path.dirname(__file__), 'array-place_footprints.svg.png')

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

        _pcbnew_frame = [x for x in wx.GetTopLevelWindows() if x.GetTitle().lower().startswith('pcbnew')][0]

        # check if there is exactly one module selected
        selected_modules = [x for x in pcbnew.GetBoard().GetModules() if x.IsSelected()]
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
            # by ref
            module_reference_designator = ''.join(i for i in pivot_module_reference if not i.isdigit())
            module_reference_number = int(''.join(i for i in pivot_module_reference if i.isdigit()))

            # get list of all modules with same reference designator
            list_of_all_modules_with_same_designator = placer.get_modules_with_reference_designator(module_reference_designator)
            sorted_list = natural_sort(list_of_all_modules_with_same_designator)

            list_of_consecutive_modules=[]
            start_index = sorted_list.index(pivot_module_reference)
            count_start = module_reference_number
            for mod in sorted_list[start_index:]:
                if int(''.join(i for i in mod if i.isdigit())) == count_start:
                    count_start = count_start + 1
                    list_of_consecutive_modules.append(mod)
                else:
                    break

            count_start = module_reference_number
            reversed_list = list(reversed(sorted_list))
            start_index = reversed_list.index(pivot_module_reference)
            for mod in reversed_list[start_index:]:
                if int(''.join(i for i in mod if i.isdigit())) == count_start:
                    count_start = count_start -1
                    list_of_consecutive_modules.append(mod)
                else:
                    break

            sorted_modules = natural_sort(list(set(list_of_consecutive_modules)))

            # display dialog
            dlg = PlaceByReference(_pcbnew_frame, placer, pivot_module_reference, user_units)
            dlg.list_modules.AppendItems(sorted_modules)

            # by default select all sheets
            number_of_items = dlg.list_modules.GetCount()
            for i in range(number_of_items):
                dlg.list_modules.Select(i)
            res = dlg.ShowModal()

            if res == wx.ID_CANCEL:
                return

            # get list of modules to place
            modules_to_place_indeces = dlg.list_modules.GetSelections()
            modules_to_place = natural_sort([sorted_modules[i] for i in modules_to_place_indeces])
            # get mode
            if dlg.com_arr.GetStringSelection() == u'Circular':
                delta_angle = float(dlg.val_y_angle.GetValue())
                if user_units == 'mm':
                    radius = float(dlg.val_x_mag.GetValue())
                else:
                    radius = float(dlg.val_x_mag.GetValue())/25.4
                placer.place_circular(modules_to_place, radius, delta_angle, False)

            if dlg.com_arr.GetStringSelection() == u'Linear':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                placer.place_linear(modules_to_place, step_x, step_y)

            if dlg.com_arr.GetStringSelection() == u'Matrix':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                nr_columns = int(dlg.val_columns.GetValue())
                placer.place_matrix(sorted_modules, step_x, step_y, nr_columns)

        # by sheet
        else:
            # get list of all modules with same ID
            list_of_modules = placer.get_list_of_modules_with_same_id(pivot_module.mod_id)
            # display dialog
            dlg = PlaceBySheet(_pcbnew_frame, placer, pivot_module_reference, user_units)
            levels = pivot_module.filename
            dlg.list_levels.Clear()
            dlg.list_levels.AppendItems(levels)
            res = dlg.ShowModal()

            if res == wx.ID_CANCEL:
                return

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
            if dlg.com_arr.GetStringSelection() == u'Circular':
                delta_angle = float(dlg.val_y_angle.GetValue())
                if user_units == 'mm':
                    radius = float(dlg.val_x_mag.GetValue())
                else:
                    radius = float(dlg.val_x_mag.GetValue())/25.4
                placer.place_circular(sorted_modules, radius, delta_angle, True)

            if dlg.com_arr.GetStringSelection() == u'Linear':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                placer.place_linear(sorted_modules, step_x, step_y)

            if dlg.com_arr.GetStringSelection() == u'Matrix':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                nr_columns = int(dlg.val_columns.GetValue())
                placer.place_matrix(sorted_modules, step_x, step_y, nr_columns)

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
