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
## Class Pad2PadTrackDistanceGUI
###########################################################################

class Pad2PadTrackDistanceGUI ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Pad2pad track distance", pos = wx.DefaultPosition, size = wx.Size( 274,139 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bSizer4 = wx.BoxSizer( wx.VERTICAL )
		
		fgSizer1 = wx.FlexGridSizer( 2, 2, 0, 0 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"Distance between pads is:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )
		fgSizer1.Add( self.m_staticText2, 0, wx.ALL, 5 )
		
		self.lbl_length = wx.StaticText( self, wx.ID_ANY, u"0.0 mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_length.Wrap( -1 )
		fgSizer1.Add( self.lbl_length, 0, wx.ALL, 5 )
		
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"Resistance between pads is:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		fgSizer1.Add( self.m_staticText3, 0, wx.ALL, 5 )
		
		self.lbl_resistance = wx.StaticText( self, wx.ID_ANY, u"0.0 mOhm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_resistance.Wrap( -1 )
		fgSizer1.Add( self.lbl_resistance, 0, wx.ALL, 5 )
		
		
		bSizer4.Add( fgSizer1, 1, wx.EXPAND, 5 )
		
		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btn_highlight = wx.Button( self, wx.ID_ANY, u"Highlight", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.btn_highlight, 0, wx.ALL, 5 )
		
		self.btn_ok = wx.Button( self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.btn_ok, 0, wx.ALL, 5 )
		
		
		bSizer4.Add( bSizer5, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer4 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.btn_highlight.Bind( wx.EVT_BUTTON, self.highlight_tracks )
		self.btn_ok.Bind( wx.EVT_BUTTON, self.on_btn_ok )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def highlight_tracks( self, event ):
		event.Skip()
	
	def on_btn_ok( self, event ):
		event.Skip()
	

