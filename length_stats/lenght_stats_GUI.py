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
## Class LenghtStatsGUI
###########################################################################

class LenghtStatsGUI ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Lenght stats", pos = wx.DefaultPosition, size = wx.Size( 353,478 ), style = wx.DEFAULT_DIALOG_STYLE )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.net_list = wx.ListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT )
		bSizer1.Add( self.net_list, 1, wx.ALL|wx.EXPAND, 5 )
		
		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.chk_cont = wx.CheckBox( self, wx.ID_ANY, u"Continuous refresh", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.chk_cont, 0, wx.ALL, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		self.lbl_refresh_time = wx.StaticText( self, wx.ID_ANY, u"Refresh time:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_refresh_time.Wrap( -1 )
		bSizer2.Add( self.lbl_refresh_time, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer2, 0, wx.EXPAND, 5 )
		
		bSizer3 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btn_refresh = wx.Button( self, wx.ID_ANY, u"Refresh", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.btn_refresh, 0, wx.ALL, 5 )
		
		
		bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.btn_ok = wx.Button( self, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.btn_ok, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer3, 0, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		self.chk_cont.Bind( wx.EVT_CHECKBOX, self.cont_refresh_toggle )
		self.btn_refresh.Bind( wx.EVT_BUTTON, self.on_btn_refresh )
		self.btn_ok.Bind( wx.EVT_BUTTON, self.on_btn_ok )
	
	def __del__( self ):
		pass
	
	
	# Virtual event handlers, overide them in your derived class
	def cont_refresh_toggle( self, event ):
		event.Skip()
	
	def on_btn_refresh( self, event ):
		event.Skip()
	
	def on_btn_ok( self, event ):
		event.Skip()
	

