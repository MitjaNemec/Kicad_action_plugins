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
## Class PlaceByReferenceGUI
###########################################################################

class PlaceByReferenceGUI ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Place footprints", pos = wx.DefaultPosition, size = wx.Size( 257,496 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
		
		self.SetSizeHints( wx.Size( 257,-1 ), wx.DefaultSize )
		
		bSizer3 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"List of footprints:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )
		bSizer3.Add( self.m_staticText2, 0, wx.ALL, 5 )
		
		list_modulesChoices = []
		self.list_modules = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, list_modulesChoices, wx.LB_MULTIPLE|wx.LB_NEEDED_SB )
		bSizer3.Add( self.list_modules, 1, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer3.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
		
		
		bSizer3.Add( bSizer5, 0, wx.EXPAND, 5 )
		
		gSizer2 = wx.GridSizer( 1, 2, 0, 0 )
		
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Arrangement:", wx.DefaultPosition, wx.Size( 110,-1 ), 0 )
		self.m_staticText3.Wrap( -1 )
		gSizer2.Add( self.m_staticText3, 0, wx.ALL, 5 )
		
		com_arrChoices = [ u"Linear", u"Matrix", u"Circular" ]
		self.com_arr = wx.ComboBox( self, wx.ID_ANY, u"Combo!", wx.DefaultPosition, wx.Size( 110,-1 ), com_arrChoices, wx.CB_READONLY )
		self.com_arr.SetSelection( 0 )
		gSizer2.Add( self.com_arr, 0, wx.ALL, 5 )
		
		
		bSizer3.Add( gSizer2, 0, 0, 5 )
		
		self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer3.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer17 = wx.BoxSizer( wx.HORIZONTAL )
		
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
		gSizer1.Add( self.val_y_angle, 1, wx.ALL, 5 )
		
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
		
		
		bSizer17.Add( gSizer1, 0, wx.EXPAND, 5 )
		
		
		bSizer3.Add( bSizer17, 0, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer3 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.list_modules.Bind( wx.EVT_LISTBOX, self.on_selected )
		self.com_arr.Bind( wx.EVT_COMBOBOX, self.arr_changed )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def on_selected( self, event ):
		event.Skip()
	
	def arr_changed( self, event ):
		event.Skip()
	

