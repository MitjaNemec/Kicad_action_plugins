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
## Class LengthStatsGUI
###########################################################################

class LengthStatsGUI ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Length stats", pos = wx.DefaultPosition, size = wx.Size( 353,454 ), style = wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer5 = wx.BoxSizer( wx.VERTICAL )

		self.net_list = wx.ListCtrl( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT )
		bSizer5.Add( self.net_list, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		self.chk_cont = wx.CheckBox( self.m_panel1, wx.ID_ANY, u"Continuous refresh", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.chk_cont, 0, wx.ALL, 5 )

		self.m_staticline1 = wx.StaticLine( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer2.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

		self.lbl_refresh_time = wx.StaticText( self.m_panel1, wx.ID_ANY, u"Refresh time:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lbl_refresh_time.Wrap( -1 )

		bSizer2.Add( self.lbl_refresh_time, 0, wx.ALL, 5 )


		bSizer5.Add( bSizer2, 0, wx.EXPAND, 5 )

		bSizer3 = wx.BoxSizer( wx.HORIZONTAL )

		self.btn_refresh = wx.Button( self.m_panel1, wx.ID_ANY, u"Refresh", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.btn_refresh, 0, wx.ALL, 5 )

		self.m_cpy = wx.Button( self.m_panel1, wx.ID_ANY, u"Copy", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.m_cpy, 0, wx.ALL, 5 )


		bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.btn_ok = wx.Button( self.m_panel1, wx.ID_OK, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer3.Add( self.btn_ok, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )


		bSizer5.Add( bSizer3, 0, wx.EXPAND, 5 )


		self.m_panel1.SetSizer( bSizer5 )
		self.m_panel1.Layout()
		bSizer5.Fit( self.m_panel1 )
		bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.net_list.Bind( wx.EVT_LIST_COL_CLICK, self.sort_items )
		self.net_list.Bind( wx.EVT_LIST_ITEM_DESELECTED, self.item_selected )
		self.net_list.Bind( wx.EVT_LIST_ITEM_SELECTED, self.item_selected )
		self.net_list.Bind( wx.EVT_LIST_KEY_DOWN, self.delete_items )
		self.chk_cont.Bind( wx.EVT_CHECKBOX, self.cont_refresh_toggle )
		self.btn_refresh.Bind( wx.EVT_BUTTON, self.on_btn_refresh )
		self.m_cpy.Bind( wx.EVT_BUTTON, self.copy_items )
		self.btn_ok.Bind( wx.EVT_BUTTON, self.on_btn_ok )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def sort_items( self, event ):
		event.Skip()

	def item_selected( self, event ):
		event.Skip()


	def delete_items( self, event ):
		event.Skip()

	def cont_refresh_toggle( self, event ):
		event.Skip()

	def on_btn_refresh( self, event ):
		event.Skip()

	def copy_items( self, event ):
		event.Skip()

	def on_btn_ok( self, event ):
		event.Skip()


