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
## Class DeleteSelectedGUI
###########################################################################

class DeleteSelectedGUI ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Delete selected", pos = wx.DefaultPosition, size = wx.Size( 223,200 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer3 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText1 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"Delete selected", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		bSizer3.Add( self.m_staticText1, 0, wx.ALL, 5 )
		
		self.chkbox_tracks = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Tracks", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.chkbox_tracks.SetValue(True) 
		bSizer3.Add( self.chkbox_tracks, 0, wx.ALL, 5 )
		
		self.chkbox_zones = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Zones", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.chkbox_zones, 0, wx.ALL, 5 )
		
		self.chkbox_modules = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Footprints", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.chkbox_modules, 0, wx.ALL, 5 )
		
		
		self.m_panel1.SetSizer( bSizer3 )
		self.m_panel1.Layout()
		bSizer3.Fit( self.m_panel1 )
		bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )
		
		bSizer31 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btn_ok = wx.Button( self, wx.ID_OK, u"Ok", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer31.Add( self.btn_ok, 0, wx.ALL, 5 )
		
		self.btn_cancel = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer31.Add( self.btn_cancel, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer31, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
	

