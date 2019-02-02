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
import pcbnew
import Tkinter as tk
import tkMessageBox
import threading


class NoWxpython(pcbnew.ActionPlugin):
    """
    Notify user of missing wxpython
    """
    def defaults(self):
        self.name = "Replicate layout"
        self.category = "Modify Drawing PCB"
        self.description = "Replicate layout of a hierchical sheet"

    def Run(self):
        def messagebox_task():
            root = tk.Tk()
            root.wm_attributes("-topmost", "true")
            root.withdraw()
            root.update_idletasks()
            root.grab_set()
            mb = tkMessageBox.showerror("Replicate layout", "Error while registering plugin.\nMost likely Wxpython is not supported with this KiCad build.")
            root.destroy()
        t = threading.Thread(target=messagebox_task)
        t.start()
        t.join()

