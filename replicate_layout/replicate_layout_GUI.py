# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class ReplicateLayoutGUI
###########################################################################

class ReplicateLayoutGUI ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Replicate layout", pos = wx.DefaultPosition, size = wx.Size( 313,492 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )

		self.SetSizeHints( wx.Size( 313,409 ), wx.DefaultSize )

		bSizer14 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"Source hierarchy level:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		bSizer14.Add( self.m_staticText5, 0, wx.ALL, 5 )

		bSizer18 = wx.BoxSizer( wx.HORIZONTAL )

		list_levelsChoices = []
		self.list_levels = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 230,-1 ), list_levelsChoices, 0 )
		bSizer18.Add( self.list_levels, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer14.Add( bSizer18, 1, wx.EXPAND, 5 )

		self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"Destination sheets:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		bSizer14.Add( self.m_staticText6, 0, wx.ALL, 5 )

		bSizer16 = wx.BoxSizer( wx.HORIZONTAL )

		list_sheetsChoices = []
		self.list_sheets = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( 230,-1 ), list_sheetsChoices, wx.LB_MULTIPLE|wx.LB_NEEDED_SB )
		bSizer16.Add( self.list_sheets, 1, wx.ALL|wx.EXPAND, 5 )


		bSizer14.Add( bSizer16, 2, wx.EXPAND, 5 )

		self.chkbox_locked = wx.CheckBox( self, wx.ID_ANY, u"Replicate locked footprints", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.chkbox_locked, 0, wx.ALL, 5 )

		self.chkbox_tracks = wx.CheckBox( self, wx.ID_ANY, u"Replicate tracks", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkbox_tracks.SetValue(True)
		bSizer14.Add( self.chkbox_tracks, 0, wx.ALL, 5 )

		self.chkbox_zones = wx.CheckBox( self, wx.ID_ANY, u"Replicate zones", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkbox_zones.SetValue(True)
		bSizer14.Add( self.chkbox_zones, 0, wx.ALL, 5 )

		self.chkbox_text = wx.CheckBox( self, wx.ID_ANY, u"Replicate text", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkbox_text.SetValue(True)
		bSizer14.Add( self.chkbox_text, 0, wx.ALL, 5 )

		self.chkbox_drawings = wx.CheckBox( self, wx.ID_ANY, u"Replicate drawings", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkbox_drawings.SetValue(True)
		bSizer14.Add( self.chkbox_drawings, 0, wx.ALL, 5 )

		self.chkbox_intersecting = wx.CheckBox( self, wx.ID_ANY, u"Replicate intersecting tracks/zones/drawings", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.chkbox_intersecting, 0, wx.ALL, 5 )

		self.chkbox_remove = wx.CheckBox( self, wx.ID_ANY, u"Remove existing tracks/zones/drawings", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.chkbox_remove, 0, wx.ALL, 5 )

		self.chkbox_remove_duplicates = wx.CheckBox( self, wx.ID_ANY, u"Remove duplicates (might take some time)", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer14.Add( self.chkbox_remove_duplicates, 0, wx.ALL, 5 )

		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_ok = wx.Button( self, wx.ID_OK, u"Ok", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer15.Add( self.btn_ok, 0, wx.ALL, 5 )

		self.btn_cancel = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer15.Add( self.btn_cancel, 0, wx.ALL, 5 )


		bSizer14.Add( bSizer15, 0, 0, 5 )


		self.SetSizer( bSizer14 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.OnCancel )
		self.list_levels.Bind( wx.EVT_LISTBOX, self.level_changed )
		self.btn_ok.Bind( wx.EVT_BUTTON, self.OnOk )
		self.btn_cancel.Bind( wx.EVT_BUTTON, self.OnCancel )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def OnCancel( self, event ):
		event.Skip()

	def level_changed( self, event ):
		event.Skip()

	def OnOk( self, event ):
		event.Skip()



