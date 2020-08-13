# -*- coding: utf-8 -*- 

###########################################################################
## Python code generated with wxFormBuilder (version Jun 17 2015)
## http://www.wxformbuilder.org/
##
## PLEASE DO "NOT" EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class MainDialog
###########################################################################

class MainDialog ( wx.Dialog ):
	
	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Security Mesh Generator Plugin", pos = wx.DefaultPosition, size = wx.Size( 496,258 ), style = wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.STAY_ON_TOP )
		
		self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_scrolledWindow1 = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.m_scrolledWindow1.SetScrollRate( 5, 5 )
		fgSizer1 = wx.FlexGridSizer( 3, 2, 0, 0 )
		fgSizer1.AddGrowableCol( 1 )
		fgSizer1.SetFlexibleDirection( wx.VERTICAL )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )
		
		self.m_staticText1 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Mesh net name prefix", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		fgSizer1.Add( self.m_staticText1, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		self.m_net_prefix = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, u"mesh-", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_net_prefix, 2, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5 )
		
		
		fgSizer1.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_netLabel = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"0 matching nets", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_netLabel.Wrap( -1 )
		fgSizer1.Add( self.m_netLabel, 0, wx.ALL, 5 )
		
		self.m_staticText3 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Mesh angle", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		fgSizer1.Add( self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_angleInput = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, u"0.00", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_angleInput, 0, wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_staticText5 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"° (deg)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		bSizer4.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		
		fgSizer1.Add( bSizer4, 1, wx.EXPAND, 5 )
		
		self.m_staticText4 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Trace width", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		fgSizer1.Add( self.m_staticText4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_traceInput = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, u"0.127", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer5.Add( self.m_traceInput, 0, wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_spinBtn1 = wx.SpinButton( self.m_scrolledWindow1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_VERTICAL )
		bSizer5.Add( self.m_spinBtn1, 0, wx.ALL, 5 )
		
		self.m_staticText6 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )
		bSizer5.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		
		fgSizer1.Add( bSizer5, 1, wx.EXPAND, 5 )
		
		self.m_staticText7 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Space width", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		fgSizer1.Add( self.m_staticText7, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )
		
		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_spaceInput = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, u"0.127", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer6.Add( self.m_spaceInput, 0, wx.ALIGN_CENTER_VERTICAL, 5 )
		
		self.m_spinBtn2 = wx.SpinButton( self.m_scrolledWindow1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.SP_VERTICAL )
		bSizer6.Add( self.m_spinBtn2, 0, wx.ALL, 5 )
		
		self.m_staticText8 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )
		bSizer6.Add( self.m_staticText8, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		
		fgSizer1.Add( bSizer6, 1, wx.EXPAND, 5 )
		
		
		self.m_scrolledWindow1.SetSizer( fgSizer1 )
		self.m_scrolledWindow1.Layout()
		fgSizer1.Fit( self.m_scrolledWindow1 )
		bSizer1.Add( self.m_scrolledWindow1, 1, wx.EXPAND |wx.ALL, 5 )
		
		bSizer99 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_cancelButton = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_cancelButton, 0, wx.ALL, 5 )
		
		
		bSizer99.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )
		
		self.m_removeButton = wx.Button( self, wx.ID_ANY, u"Remove Mesh Traces", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_removeButton, 0, wx.ALL, 5 )
		
		self.m_generateButton = wx.Button( self, wx.ID_ANY, u"Generate", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_generateButton, 0, wx.ALL, 5 )
		
		
		bSizer1.Add( bSizer99, 0, wx.ALL|wx.EXPAND, 3 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
	

