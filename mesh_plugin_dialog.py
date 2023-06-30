# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-367-gf0e67a69)
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
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Security Mesh Generator Plugin", pos = wx.DefaultPosition, size = wx.Size( 632,458 ), style = wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.STAY_ON_TOP )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		fgSizer1 = wx.FlexGridSizer( 0, 2, 0, 0 )
		fgSizer1.AddGrowableCol( 1 )
		fgSizer1.SetFlexibleDirection( wx.BOTH )
		fgSizer1.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Mesh net name prefix", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		fgSizer1.Add( self.m_staticText1, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_net_prefix = wx.TextCtrl( self, wx.ID_ANY, u"mesh", wx.DefaultPosition, wx.DefaultSize, 0 )
		fgSizer1.Add( self.m_net_prefix, 2, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5 )


		fgSizer1.Add( ( 0, 0), 0, wx.EXPAND, 5 )

		self.m_netLabel = wx.StaticText( self, wx.ID_ANY, u"0 matching nets", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_netLabel.Wrap( -1 )

		fgSizer1.Add( self.m_netLabel, 0, wx.ALL, 5 )

		self.m_staticText261 = wx.StaticText( self, wx.ID_ANY, u"Board edge clearance", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText261.Wrap( -1 )

		fgSizer1.Add( self.m_staticText261, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer51 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_edgeClearanceSpin = wx.SpinCtrlDouble( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 1.500000, 0.1 )
		self.m_edgeClearanceSpin.SetDigits( 3 )
		bSizer51.Add( self.m_edgeClearanceSpin, 0, wx.ALL, 5 )

		self.m_staticText61 = wx.StaticText( self, wx.ID_ANY, u"mm", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText61.Wrap( -1 )

		bSizer51.Add( self.m_staticText61, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer51, 1, wx.EXPAND, 5 )

		self.m_staticText20 = wx.StaticText( self, wx.ID_ANY, u"Chamfer depth", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.Wrap( -1 )

		fgSizer1.Add( self.m_staticText20, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer10 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_chamferSpin = wx.SpinCtrlDouble( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 50, 25 )
		self.m_chamferSpin.SetDigits( 2 )
		bSizer10.Add( self.m_chamferSpin, 0, wx.ALL, 5 )

		self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, u"% (percent)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )

		bSizer10.Add( self.m_staticText21, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )


		fgSizer1.Add( bSizer10, 1, wx.EXPAND, 5 )

		self.m_staticText23 = wx.StaticText( self, wx.ID_ANY, u"Mesh outline layer", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )

		fgSizer1.Add( self.m_staticText23, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		m_maskLayerChoiceChoices = []
		self.m_maskLayerChoice = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, m_maskLayerChoiceChoices, wx.CB_READONLY )
		fgSizer1.Add( self.m_maskLayerChoice, 0, wx.ALL, 5 )

		self.m_staticText24 = wx.StaticText( self, wx.ID_ANY, u"Random seed", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText24.Wrap( -1 )

		fgSizer1.Add( self.m_staticText24, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_seedInput = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer11.Add( self.m_seedInput, 0, wx.ALL, 5 )

		self.m_staticText25 = wx.StaticText( self, wx.ID_ANY, u"Leave empty for random seed", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText25.Wrap( -1 )

		bSizer11.Add( self.m_staticText25, 0, wx.ALL, 5 )


		fgSizer1.Add( bSizer11, 1, wx.EXPAND, 5 )

		self.m_staticText26 = wx.StaticText( self, wx.ID_ANY, u"Anchor footprint ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText26.Wrap( -1 )

		fgSizer1.Add( self.m_staticText26, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		m_anchorChoiceChoices = []
		self.m_anchorChoice = wx.ComboBox( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, m_anchorChoiceChoices, wx.CB_READONLY )
		fgSizer1.Add( self.m_anchorChoice, 0, wx.ALL, 5 )

		self.m_staticText28 = wx.StaticText( self, wx.ID_ANY, u"Routing randomness", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText28.Wrap( -1 )

		fgSizer1.Add( self.m_staticText28, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer12 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_randomnessSpin = wx.SpinCtrlDouble( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 25, 25 )
		self.m_randomnessSpin.SetDigits( 0 )
		bSizer12.Add( self.m_randomnessSpin, 0, wx.ALL, 5 )

		self.m_staticText211 = wx.StaticText( self, wx.ID_ANY, u"% (percent)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText211.Wrap( -1 )

		bSizer12.Add( self.m_staticText211, 0, wx.ALL, 5 )


		fgSizer1.Add( bSizer12, 1, wx.EXPAND, 5 )


		bSizer1.Add( fgSizer1, 1, wx.EXPAND, 5 )

		bSizer99 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_cancelButton = wx.Button( self, wx.ID_ANY, u"Close", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer99.Add( self.m_cancelButton, 0, wx.ALL, 5 )


		bSizer99.Add( ( 0, 0), 1, wx.EXPAND, 5 )

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


