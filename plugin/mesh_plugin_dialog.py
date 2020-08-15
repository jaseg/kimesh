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
## Class MainDialog
###########################################################################

class MainDialog ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Security Mesh Generator Plugin", pos = wx.DefaultPosition, size = wx.Size( 809,762 ), style = wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.STAY_ON_TOP )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_scrolledWindow1 = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.m_scrolledWindow1.SetScrollRate( 5, 5 )
		fgSizer1 = wx.FlexGridSizer( 8, 2, 0, 0 )
		fgSizer1.AddGrowableCol( 1 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText1 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Mesh net name prefix", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		fgSizer1.Add( self.m_staticText1, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_net_prefix = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, u"mesh", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_net_prefix, 2, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 0, wx.EXPAND, 5 )

		self.m_netLabel = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"0 matching nets", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_netLabel.Wrap( -1 )

		fgSizer1.Add( self.m_netLabel, 0, wx.ALL, 5 )

		self.m_staticText3 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Mesh angle", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		fgSizer1.Add( self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_angleSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS|wx.SP_WRAP, 0, 360, 0.000000, 1 )
		self.m_angleSpin.SetDigits( 2 )
		bSizer4.Add( self.m_angleSpin, 0, wx.ALL, 5 )

		self.m_staticText5 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"° (deg)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		bSizer4.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer4, 1, wx.EXPAND, 5 )

		self.m_staticText4 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Trace width", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		fgSizer1.Add( self.m_staticText4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_traceSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 0.127, 0.1 )
		self.m_traceSpin.SetDigits( 3 )
		bSizer5.Add( self.m_traceSpin, 0, wx.ALL, 5 )

		self.m_staticText6 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		bSizer5.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer5, 1, wx.EXPAND, 5 )

		self.m_staticText7 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Space width", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		fgSizer1.Add( self.m_staticText7, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_spaceSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 0.127, 0.1 )
		self.m_spaceSpin.SetDigits( 3 )
		bSizer6.Add( self.m_spaceSpin, 0, wx.ALL, 5 )

		self.m_staticText8 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText8.Wrap( -1 )

		bSizer6.Add( self.m_staticText8, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer6, 1, wx.EXPAND, 5 )

		self.m_staticText11 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Anchor exit direction", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		fgSizer1.Add( self.m_staticText11, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer41 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_exitSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS|wx.SP_WRAP, 0, 360, 0.000000, 45 )
		self.m_exitSpin.SetDigits( 0 )
		bSizer41.Add( self.m_exitSpin, 0, wx.ALL, 5 )

		self.m_staticText51 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"° (deg)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText51.Wrap( -1 )

		bSizer41.Add( self.m_staticText51, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer41, 1, wx.EXPAND, 5 )

		self.m_staticText12 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Number of mesh traces", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		fgSizer1.Add( self.m_staticText12, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_traceCountSpin = wx.SpinCtrl( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 2 )
		fgSizer1.Add( self.m_traceCountSpin, 1, wx.ALL, 5 )

		self.m_staticText13 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Mesh origin offset", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		fgSizer1.Add( self.m_staticText13, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText15 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"x", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )

		bSizer9.Add( self.m_staticText15, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.m_offsetXSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -100, 100, 0, 0.1 )
		self.m_offsetXSpin.SetDigits( 3 )
		bSizer9.Add( self.m_offsetXSpin, 0, wx.ALL, 5 )

		self.m_staticText17 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText17.Wrap( -1 )

		bSizer9.Add( self.m_staticText17, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.m_staticText16 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"y", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )

		bSizer9.Add( self.m_staticText16, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		self.m_offsetYSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -100, 100, 0, 0.1 )
		self.m_offsetYSpin.SetDigits( 3 )
		bSizer9.Add( self.m_offsetYSpin, 0, wx.ALL, 5 )

		self.m_staticText18 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )

		bSizer9.Add( self.m_staticText18, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer9, 2, wx.EXPAND, 5 )

		self.m_staticText20 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Chamfer depth", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.Wrap( -1 )

		fgSizer1.Add( self.m_staticText20, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer10 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_chamferSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 50, 25 )
		self.m_chamferSpin.SetDigits( 2 )
		bSizer10.Add( self.m_chamferSpin, 0, wx.ALL, 5 )

		self.m_staticText21 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"% (percent)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )

		bSizer10.Add( self.m_staticText21, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer10, 1, wx.EXPAND, 5 )

		self.m_staticText22 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Layer", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )

		fgSizer1.Add( self.m_staticText22, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		m_layerChoiceChoices = []
		self.m_layerChoice = wx.Choice( self.m_scrolledWindow1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_layerChoiceChoices, 0 )
		self.m_layerChoice.SetSelection( 0 )
		fgSizer1.Add( self.m_layerChoice, 0, wx.ALL, 5 )

		self.m_staticText23 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Mesh outline layer", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )

		fgSizer1.Add( self.m_staticText23, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		m_maskLayerChoiceChoices = []
		self.m_maskLayerChoice = wx.Choice( self.m_scrolledWindow1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_maskLayerChoiceChoices, 0 )
		self.m_maskLayerChoice.SetSelection( 0 )
		fgSizer1.Add( self.m_maskLayerChoice, 0, wx.ALL, 5 )

		self.m_staticText24 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Random seed", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )

		fgSizer1.Add( self.m_staticText24, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_seedInput = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer11.Add( self.m_seedInput, 0, wx.ALL, 5 )

		self.m_staticText25 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Leave empty for random seed", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )

		bSizer11.Add( self.m_staticText25, 0, wx.ALL, 5 )


		fgSizer1.Add( bSizer11, 1, wx.EXPAND, 5 )

		self.m_staticText26 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Anchor footprint designator", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )

		fgSizer1.Add( self.m_staticText26, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_anchorInput = wx.TextCtrl( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_anchorInput, 0, wx.ALL, 5 )

		self.m_staticText28 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"Routing randomness", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText28.Wrap( -1 )

		fgSizer1.Add( self.m_staticText28, 0, wx.ALL, 5 )

		bSizer12 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_randomnessSpin = wx.SpinCtrlDouble( self.m_scrolledWindow1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 25, 25 )
		self.m_randomnessSpin.SetDigits( 0 )
		bSizer12.Add( self.m_randomnessSpin, 0, wx.ALL, 5 )

		self.m_staticText211 = wx.StaticText( self.m_scrolledWindow1, wx.ID_ANY, u"% (percent)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText211.Wrap( -1 )

		bSizer12.Add( self.m_staticText211, 0, wx.ALL, 5 )


		fgSizer1.Add( bSizer12, 1, wx.EXPAND, 5 )


		self.m_scrolledWindow1.SetSizer( fgSizer1 )
		self.m_scrolledWindow1.Layout()
		fgSizer1.Fit( self.m_scrolledWindow1 )
		bSizer1.Add( self.m_scrolledWindow1, 1, wx.EXPAND |wx.ALL, 5 )

		bSizer99 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_cancelButton = wx.Button( self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_cancelButton, 0, wx.ALL, 5 )


		bSizer99.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.m_removeAllButton = wx.Button( self, wx.ID_ANY, u"Remove All Mesh Traces", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_removeAllButton, 0, wx.ALL, 5 )

		self.m_removeButton = wx.Button( self, wx.ID_ANY, u"Remove Matching Mesh Traces", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_removeButton, 0, wx.ALL, 5 )

		self.m_generateButton = wx.Button( self, wx.ID_ANY, u"Generate", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_generateButton, 0, wx.ALL, 5 )


		bSizer1.Add( bSizer99, 0, wx.ALL|wx.EXPAND, 3 )


		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


