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
## Class InitialDialogGUI
###########################################################################

class InitialDialogGUI ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Save/Restore Layout", pos = wx.DefaultPosition, size = wx.Size( 242,74 ), style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.btn_save = wx.Button( self, wx.ID_OK, u"Save layout", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btn_save, 0, wx.ALL, 5 )
		
		self.btn_restore = wx.Button( self, wx.ID_CANCEL, u"Restore layout", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer2.Add( self.btn_restore, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer2, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
	

