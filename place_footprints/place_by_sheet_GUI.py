# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Nov  6 2017)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class PlaceBySheetGUI
###########################################################################

class PlaceBySheetGUI ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Place footprints", pos = wx.DefaultPosition, size = wx.Size( 258,553 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
		
		self.SetSizeHints( wx.Size( 258,409 ), wx.DefaultSize )
		
		bSizer14 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"Hierarchy level:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		bSizer14.Add( self.m_staticText5, 0, wx.ALL, 5 )
		
		bSizer18 = wx.BoxSizer( wx.HORIZONTAL )
		
		list_levelsChoices = []
		self.list_levels = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 230,-1 ), list_levelsChoices, 0 )
		bSizer18.Add( self.list_levels, 1, wx.ALL|wx.EXPAND, 5 )
		
		
		bSizer14.Add( bSizer18, 1, wx.EXPAND, 5 )
		
		self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Sheets to replicate:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )
		bSizer14.Add( self.m_staticText6, 0, wx.ALL, 5 )
		
		bSizer16 = wx.BoxSizer( wx.HORIZONTAL )
		
		list_sheetsChoices = []
		self.list_sheets = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 230,-1 ), list_sheetsChoices, wx.LB_MULTIPLE|wx.LB_NEEDED_SB )
		bSizer16.Add( self.list_sheets, 1, wx.ALL|wx.EXPAND, 5 )
		
		
		bSizer14.Add( bSizer16, 2, wx.EXPAND, 5 )
		
		self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer14.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )
		
		gSizer2 = wx.GridSizer( 0, 2, 0, 0 )
		
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Arrangement:", wx.DefaultPosition, wx.Size( 110,-1 ), 0 )
		self.m_staticText3.Wrap( -1 )
		gSizer2.Add( self.m_staticText3, 0, wx.ALL, 5 )
		
		com_arrChoices = [ u"Linear", u"Matrix", u"Circular" ]
		self.com_arr = wx.ComboBox( self, wx.ID_ANY, u"Combo!", wx.DefaultPosition, wx.Size( 110,-1 ), com_arrChoices, wx.CB_READONLY )
		self.com_arr.SetSelection( 0 )
		gSizer2.Add( self.com_arr, 0, wx.ALL, 5 )
		
		
		bSizer14.Add( gSizer2, 0, 0, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer14.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
		
		gSizer1 = wx.GridSizer( 4, 2, 0, 0 )
		
		self.lbl_x_mag = wx.StaticText( self, wx.ID_ANY, u"step x (mm):", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_x_mag.Wrap( -1 )
		gSizer1.Add( self.lbl_x_mag, 0, wx.ALL, 5 )
		
		self.val_x_mag = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.val_x_mag, 0, wx.ALL, 5 )
		
		self.lbl_y_angle = wx.StaticText( self, wx.ID_ANY, u"step y (mm):", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_y_angle.Wrap( -1 )
		gSizer1.Add( self.lbl_y_angle, 0, wx.ALL, 5 )
		
		self.val_y_angle = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.val_y_angle, 0, wx.ALL, 5 )
		
		self.lbl_columns = wx.StaticText( self, wx.ID_ANY, u"Nr. columns:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_columns.Wrap( -1 )
		self.lbl_columns.Hide()
		
		gSizer1.Add( self.lbl_columns, 0, wx.ALL, 5 )
		
		self.val_columns = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.val_columns.Hide()
		
		gSizer1.Add( self.val_columns, 0, wx.ALL, 5 )
		
		self.btn_ok = wx.Button( self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.btn_ok, 0, wx.ALL, 5 )
		
		self.btn_cancel = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		gSizer1.Add( self.btn_cancel, 0, wx.ALL, 5 )
		
		
		bSizer6.Add( gSizer1, 0, wx.EXPAND, 5 )
		
		
		bSizer14.Add( bSizer6, 0, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer14 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.list_levels.Bind( wx.EVT_LISTBOX, self.level_changed )
		self.list_sheets.Bind( wx.EVT_LISTBOX, self.on_selected )
		self.com_arr.Bind( wx.EVT_COMBOBOX, self.arr_changed )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def level_changed( self, event ):
		event.Skip()
	
	def on_selected( self, event ):
		event.Skip()
	
	def arr_changed( self, event ):
		event.Skip()
	

