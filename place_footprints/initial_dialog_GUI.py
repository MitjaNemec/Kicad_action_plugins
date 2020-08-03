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
## Class InitialDialogGUI
###########################################################################

class InitialDialogGUI ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Place footprints", pos = wx.DefaultPosition, size = wx.Size( 322,107 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Place by?", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		bSizer1.Add( self.m_staticText1, 0, wx.ALL, 5 )

		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_selection = wx.Button( self, wx.ID_ANY, u"Selection", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btn_selection, 0, wx.ALL, 5 )

		self.btn_reference = wx.Button( self, wx.ID_ANY, u"Reference nr.", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btn_reference, 0, wx.ALL, 5 )

		self.btn_sheet = wx.Button( self, wx.ID_ANY, u"Sheet nr.", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btn_sheet, 0, wx.ALL, 5 )


		bSizer1.Add( bSizer2, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.btn_selection.Bind( wx.EVT_BUTTON, self.evt_selection )
		self.btn_reference.Bind( wx.EVT_BUTTON, self.evt_reference )
		self.btn_sheet.Bind( wx.EVT_BUTTON, self.evt_sheet )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def evt_selection( self, event ):
		event.Skip()

	def evt_reference( self, event ):
		event.Skip()

	def evt_sheet( self, event ):
		event.Skip()


