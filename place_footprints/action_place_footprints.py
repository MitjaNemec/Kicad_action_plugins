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
import os
import logging
import sys
import math
import re
# import place_footprints
if __name__ == '__main__':
    import place_footprints
    import initial_dialog_GUI
    import place_by_reference_GUI
    import place_by_sheet_GUI
else:
    from . import place_footprints
    from . import initial_dialog_GUI
    from . import place_by_reference_GUI
    from . import place_by_sheet_GUI


# get version information
version_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "version.txt")
with open(version_filename) as f:
    VERSION = f.readline().strip()

# > V5.1.5 and V 5.99 build information
if hasattr(pcbnew, 'GetBuildVersion'):
    BUILD_VERSION = pcbnew.GetBuildVersion()
else:
    BUILD_VERSION = "Unknown"


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
    return sorted(l, key=alphanum_key)


def set_highlight_on_module(module):
    pads_list = module.Pads()
    for pad in pads_list:
        pad.SetBrightened()
    drawings = module.GraphicalItems()
    for item in drawings:
        item.SetBrightened()


def clear_highlight_on_module(module):
    pads_list = module.Pads()
    for pad in pads_list:
        pad.ClearBrightened()
    drawings = module.GraphicalItems()
    for item in drawings:
        item.ClearBrightened()   


class PlaceBySheet(place_by_sheet_GUI.PlaceBySheetGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO nothing
        pass

    # Virtual event handlers, overide them in your derived class
    def level_changed(self, event):
        index = self.list_levels.GetSelection()

        self.list_sheetsChoices = self.placer.get_sheets_to_replicate(self.pivot_mod, self.pivot_mod.sheet_id[index])

        # clear highlights
        for ref in self.ref_list:
            module = self.placer.get_mod_by_ref(ref)
            clear_highlight_on_module(module.mod)
        pcbnew.Refresh()

        # get anchor modules
        anchor_modules = self.placer.get_list_of_modules_with_same_id(self.pivot_mod.mod_id)

        # find matching anchors to maching sheets
        self.ref_list = []
        for sheet in self.list_sheetsChoices:
            for mod in anchor_modules:
                if "/".join(sheet) in "/".join(mod.sheet_id):
                    self.ref_list.append(mod.ref)
                    break

        sheets_for_list = ['/'.join(x[0]) + " (" + x[1] + ")" for x in zip(self.list_sheetsChoices, self.ref_list)]

        self.list_sheets.Clear()
        self.list_sheets.AppendItems(sheets_for_list)

        # by default select all sheets
        number_of_items = self.list_sheets.GetCount()
        for i in range(number_of_items):
            self.list_sheets.Select(i)

        # highlight all modules
        for ref in self.ref_list:
            module = self.placer.get_mod_by_ref(ref)
            set_highlight_on_module(module.mod)
        pcbnew.Refresh()        

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

            self.val_columns.Clear()
            self.val_columns.SetValue(str(int(round(math.sqrt(len(self.list_sheets.GetSelections()))))))

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
            # presume square arrangement,
            # thus the number of columns should be equal to number of rows
            self.val_columns.Clear()
            self.val_columns.SetValue(str(int(round(math.sqrt(len(self.list_sheets.GetSelections()))))))

        # circular layout
        if self.com_arr.GetStringSelection() == u"Circular":
            number_of_all_sheets = len(self.list_sheets.GetSelections())
            circumference = number_of_all_sheets * self.width
            radius = circumference / (2 * math.pi)
            angle = 360.0 / (number_of_all_sheets+1)
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
        self.ref_list = []
        self.list_sheetsChoices = None

        modules = self.placer.get_modules_on_sheet(self.pivot_mod.sheet_id)
        self.height, self.width = self.placer.get_modules_bounding_box(modules)

    def on_selected(self, event):
        # go throught the list and set/clear higliht acordingly
        nr_items = self.list_sheets.GetCount()
        for i in range(nr_items):
            mod_ref = self.ref_list[i]
            module = self.placer.get_mod_by_ref(mod_ref)
            mod = module.mod
            if self.list_sheets.IsSelected(i):
                set_highlight_on_module(mod)
            else:
                clear_highlight_on_module(mod)
        pcbnew.Refresh()


class PlaceByReference(place_by_reference_GUI.PlaceByReferenceGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO NOTHING
        pass

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
        # Matrix
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

            self.val_columns.Clear()
            self.val_columns.SetValue(str(int(round(math.sqrt(len(self.list_modules.GetSelections()))))))
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

    def on_selected(self, event):
        # go throught the list and set/clear higliht acordingly
        nr_items = self.list_modules.GetCount()
        for i in range(nr_items):
            mod_ref = self.list_modules.GetString(i)
            module = self.placer.get_mod_by_ref(mod_ref)
            mod = module.mod
            if self.list_modules.IsSelected(i):
                set_highlight_on_module(mod)
            else:
                clear_highlight_on_module(mod)
        pcbnew.Refresh()


class InitialDialog(initial_dialog_GUI.InitialDialogGUI):
    # hack for new wxFormBuilder generating code incompatible with old wxPython
    # noinspection PyMethodOverriding
    def SetSizeHints(self, sz1, sz2):
        # DO NOTHING
        pass

    def __init__(self, parent):
        initial_dialog_GUI.InitialDialogGUI.__init__(self, parent)


class PlaceFootprints(pcbnew.ActionPlugin):
    """
    A script to replicate layout
    How to use:
    - move to GAL
    - select footprint of layout to replicate
    - call the plugin
    - enter pivot step and confirm pivot footprint
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

        # Remove all handlers associated with the root logger object.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # set up logger
        logging.basicConfig(level=logging.DEBUG,
                            filename="place_footprints.log",
                            filemode='w',
                            format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                            datefmt='%m-%d %H:%M:%S')
        logger = logging.getLogger(__name__)
        logger.info("Plugin executed on: " + repr(sys.platform))
        logger.info("Plugin executed with python version: " + repr(sys.version))
        logger.info("KiCad build version: " + BUILD_VERSION)
        logger.info("Place footprints plugin version: " + VERSION + " started")

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
            message = "More or less than 1 footprint selected. Please select exactly one footprint and run the script again"
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # this it the reference footprint
        pivot_module_reference = selected_names[0]

        # ask user which way to select other footprints (by increasing reference number or by ID)
        dlg = InitialDialog(_pcbnew_frame)
        res = dlg.ShowModal()

        try:
            placer = place_footprints.Placer(board)
        except LookupError as error:
            caption = 'Place footprints'
            message = str(error)
            dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            logging.shutdown()
            return

        pivot_module = placer.get_mod_by_ref(pivot_module_reference)

        # by reference number
        if res == wx.ID_OK:
            # by ref
            for i in range(len(pivot_module_reference)):
                if not pivot_module_reference[i].isdigit():
                    index = i+1
            module_reference_designator = pivot_module_reference[:index]
            module_reference_number = pivot_module_reference[index:]
            logger.info("Reference designator is: " + module_reference_designator)
            logger.info("Rerefence number is: " + module_reference_number)

            # get list of all modules with same reference designator
            list_of_all_modules_with_same_designator = placer.get_modules_with_reference_designator(module_reference_designator)

            sorted_list = sorted_data=sorted(list_of_all_modules_with_same_designator, key=lambda x : int(x[index:]))

            # find only consequtive modules
            list_of_consecutive_modules = []
            # go through the list in positive direction
            start_index = sorted_list.index(pivot_module_reference)
            count_start = int(module_reference_number)
            for mod in sorted_list[start_index:]:
                if int(mod[index:]) == count_start:
                    count_start = count_start + 1
                    list_of_consecutive_modules.append(mod)
                else:
                    break

            # go through the list in negative direction
            reversed_list = list(reversed(sorted_list))
            start_index = reversed_list.index(pivot_module_reference)
            count_start = int(module_reference_number)
            for mod in reversed_list[start_index:]:
                if int(mod[index:]) == count_start:
                    count_start = count_start - 1
                    list_of_consecutive_modules.append(mod)
                else:
                    break

            sorted_modules = natural_sort(list(set(list_of_consecutive_modules)))
            logger.info('Sorted and filtered list:\n' + repr(sorted_modules))

            # create dialog
            dlg = PlaceByReference(_pcbnew_frame, placer, pivot_module_reference, user_units)
            dlg.list_modules.AppendItems(sorted_modules)

            # highlight all modules by default
            for mod in sorted_modules:
                module = board.FindModuleByReference(mod)
                set_highlight_on_module(module)
            pcbnew.Refresh()

            # by default select all modules
            number_of_items = dlg.list_modules.GetCount()
            for i in range(number_of_items):
                dlg.list_modules.Select(i)

            # show dialog
            res = dlg.ShowModal()

            if res == wx.ID_CANCEL:
                # clear highlight all modules by default
                for mod in sorted_modules:
                    module = board.FindModuleByReference(mod)
                    clear_highlight_on_module(module)
                pcbnew.Refresh()
                return

            # get list of modules to place
            modules_to_place_indeces = dlg.list_modules.GetSelections()
            modules_to_place = natural_sort([sorted_modules[i] for i in modules_to_place_indeces])
            logger.info('Modules to place:\n' + repr(modules_to_place))
            # get mode
            if dlg.com_arr.GetStringSelection() == u'Circular':
                delta_angle = float(dlg.val_y_angle.GetValue())
                if user_units == 'mm':
                    radius = float(dlg.val_x_mag.GetValue())
                else:
                    radius = float(dlg.val_x_mag.GetValue())/25.4
                try:
                    placer.place_circular(modules_to_place, pivot_module_reference, radius, delta_angle)
                    logger.info("Placing complete")
                    logging.shutdown()
                except Exception:
                    logger.exception("Fatal error when executing place footprints")
                    caption = 'Place footprints'
                    message = "Fatal error when executing place footprints.\n"\
                            + "You can raise an issue on GiHub page.\n" \
                            + "Please attach the place_footprints.log which you should find in the project folder."
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logging.shutdown()
                    # clear highlight all modules by default
                    for mod in sorted_modules:
                        module = board.FindModuleByReference(mod)
                        clear_highlight_on_module(module)
                    pcbnew.Refresh()
                    return

            if dlg.com_arr.GetStringSelection() == u'Linear':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                try:
                    placer.place_linear(modules_to_place, pivot_module_reference, step_x, step_y)
                    logger.info("Placing complete")
                    logging.shutdown()
                except Exception:
                    logger.exception("Fatal error when executing place footprints")
                    caption = 'Place footprints'
                    message = "Fatal error when executing place footprints.\n"\
                            + "You can raise an issue on GiHub page.\n" \
                            + "Please attach the place_footprints.log which you should find in the project folder."
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logging.shutdown()
                    # clear highlight all modules by default
                    for mod in sorted_modules:
                        module = board.FindModuleByReference(mod)
                        clear_highlight_on_module(module)
                    pcbnew.Refresh()
                    return

            if dlg.com_arr.GetStringSelection() == u'Matrix':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                nr_columns = int(dlg.val_columns.GetValue())
                try:
                    placer.place_matrix(modules_to_place, pivot_module_reference, step_x, step_y, nr_columns)
                    logger.info("Placing complete")
                    logging.shutdown()
                except Exception:
                    logger.exception("Fatal error when executing place footprints")
                    caption = 'Place footprints'
                    message = "Fatal error when executing place footprints.\n"\
                            + "You can raise an issue on GiHub page.\n" \
                            + "Please attach the place_footprints.log which you should find in the project folder."
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logging.shutdown()
                    # clear highlight all modules by default
                    for mod in sorted_modules:
                        module = board.FindModuleByReference(mod)
                        clear_highlight_on_module(module)
                    pcbnew.Refresh()
                    return
            
            # clear highlight all modules by default
            for mod in sorted_modules:
                module = board.FindModuleByReference(mod)
                clear_highlight_on_module(module)
            pcbnew.Refresh()
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
                # clear highlight all modules by default
                # get the list from the GUI elements
                for module in list_of_modules:
                    clear_highlight_on_module(module.mod)
                pcbnew.Refresh()
                return

            # based on the sheet list, find all the modules with same ID
            sheets_to_place_indeces = dlg.list_sheets.GetSelections()
            sheets_to_place = [dlg.list_sheetsChoices[i] for i in sheets_to_place_indeces]

            mod_references = [pivot_module_reference]
            for mod in list_of_modules:
                if mod.sheet_id in sheets_to_place:
                    mod_references.append(mod.ref)

            logger.info("Modules to place: " + repr(mod_references))
            # sort by reference number
            sorted_modules = natural_sort(mod_references)

            # get mode
            if dlg.com_arr.GetStringSelection() == u'Circular':
                delta_angle = float(dlg.val_y_angle.GetValue())
                if user_units == 'mm':
                    radius = float(dlg.val_x_mag.GetValue())
                else:
                    radius = float(dlg.val_x_mag.GetValue())/25.4
                try:
                    placer.place_circular(sorted_modules, pivot_module_reference, radius, delta_angle)
                    logger.info("Placing complete")
                    logging.shutdown()
                except Exception:
                    logger.exception("Fatal error when executing place footprints")
                    caption = 'Place footprints'
                    message = "Fatal error when executing place footprints.\n"\
                            + "You can raise an issue on GiHub page.\n" \
                            + "Please attach the place_footprints.log which you should find in the project folder."
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logging.shutdown()

                    # clear highlight all modules by default
                    for mod in sorted_modules:
                        module = board.FindModuleByReference(mod)
                        clear_highlight_on_module(module)
                    pcbnew.Refresh()
                    return

            if dlg.com_arr.GetStringSelection() == u'Linear':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                try:
                    placer.place_linear(sorted_modules, pivot_module_reference, step_x, step_y)
                    logger.info("Placing complete")
                    logger.info("Sorted_modules: " + repr(sorted_modules))
                    logging.shutdown()
                except Exception:
                    logger.exception("Fatal error when executing place footprints")
                    caption = 'Place footprints'
                    message = "Fatal error when executing place footprints.\n"\
                            + "You can raise an issue on GiHub page.\n" \
                            + "Please attach the place_footprints.log which you should find in the project folder."
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logging.shutdown()
                    # clear highlight all modules by default
                    for mod in sorted_modules:
                        module = board.FindModuleByReference(mod)
                        clear_highlight_on_module(module)
                    pcbnew.Refresh()
                    return

            if dlg.com_arr.GetStringSelection() == u'Matrix':
                if user_units == 'mm':
                    step_x = float(dlg.val_x_mag.GetValue())
                    step_y = float(dlg.val_y_angle.GetValue())
                else:
                    step_x = float(dlg.val_x_mag.GetValue())/25.4
                    step_y = float(dlg.val_y_angle.GetValue())/25.4
                nr_columns = int(dlg.val_columns.GetValue())
                try:
                    placer.place_matrix(sorted_modules, pivot_module_reference, step_x, step_y, nr_columns)
                    logger.info("Placing complete")
                    logging.shutdown()
                except Exception:
                    logger.exception("Fatal error when executing place footprints")
                    caption = 'Place footprints'
                    message = "Fatal error when executing place footprints.\n"\
                            + "You can raise an issue on GiHub page.\n" \
                            + "Please attach the place_footprints.log which you should find in the project folder."
                    dlg = wx.MessageDialog(_pcbnew_frame, message, caption, wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
                    logging.shutdown()
                    # clear highlight all modules by default
                    for mod in sorted_modules:
                        module = board.FindModuleByReference(mod)
                        clear_highlight_on_module(module)
                    pcbnew.Refresh()
                    return

            # clear highlight all modules by default
            for mod in sorted_modules:
                module = board.FindModuleByReference(mod)
                clear_highlight_on_module(module)
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

    def flush(self, *args, **kwargs):
        """No-op for wrapper"""
        pass
