# Title: 	Table Hunter
# Description:
#		Table data spooler for Oracle.		
# Environment:
#		Python 3.5 and wxPython 3.0	
# set NLS_LANGUAGE=AMERICAN_AMERICA.WE8ISO8859P1
# set NLS_LANGUAGE=AMERICAN_AMERICA.WE8MSWIN1252
# set NLS_LANGUAGE=AMERICAN_AMERICA.AL16UTF16
#
##64 bit client
# set ORACLE_HOME=C:\app\abuzunov-local\product\11.2.0\client_1
# set PATH=%PATH%;%ORACLE_HOME%
##db password
# set table-hunter0connectors0DEVdb=manage
# 
from __future__ import print_function
__author__ = "PyDemo"
__copyright__ = "Copyright 2017, PyDemo"
__credits__ = []
__appname__='TableHunter'
__license__ = "GPL"
__title__ = "TableHunter"
__version__ = "2"
__maintainer__ = "PyDemo"
__email__ = "pydemo.git@gmail.com"
__github__=	''
__status__ = "Development" 

import wx
import os, sys
import time, imp
import win32gui
import atexit
import shutil
import pprint as pp
import cx_Oracle
from six.moves import _thread
import wx.lib.newevent
from win32com.client import gencache
import wx.lib.inspection
import wx.lib.mixins.inspection
from multiprocessing import freeze_support 
import argparse
from tc_lib import sub, send
from copy import deepcopy
from pprint import pprint
import wx.lib.mixins.listctrl as listmix
from locale import getdefaultlocale, setlocale, LC_ALL
from wx.aui import AuiManager, AuiPaneInfo, AuiToolBar, \
AUI_TB_DEFAULT_STYLE, AUI_TB_VERTICAL, AUI_TB_OVERFLOW
from wx.py import shell, version
try:
	from  urllib.parse import unquote
except ImportError:
	#Python 2.7 and before
	from urllib import unquote
import builtins
script_name=os.path.splitext(os.path.basename(__file__))[0]
builtins.pid = os.getpid()
builtins.script_name=script_name
if 1:
	import  init_job as init
	ts, JOB_NAME, IMP_DATE, HOME, log,_ = init.init()
	d=init.d
	d['script']=''
	ts_out_dir=init.ts_out_dir
home=os.path.dirname(os.path.abspath(__file__))
app_title='%s %s' % (__title__,__version__)
job_status_file=os.path.join(init.ts_dir,'%s.%s.status_%d.py' % (os.path.splitext(__file__)[0],JOB_NAME,os.getpid()))	
e=sys.exit
job_status={}
default_fullscreen_style = wx.FULLSCREEN_NOSTATUSBAR | wx.FULLSCREEN_NOBORDER | wx.FULLSCREEN_NOCAPTION
import gettext
_ = gettext.gettext
try:
	# Python 3.4+
	if sys.platform.startswith('win'):
		import multiprocessing.popen_spawn_win32 as forking
	else:
		import multiprocessing.popen_fork as forking
except ImportError:
	import multiprocessing.forking as forking
if sys.platform.startswith('win'):
	# First define a modified version of Popen.
	class _Popen(forking.Popen):
		def __init__(self, *args, **kw):
			if hasattr(sys, 'frozen'):
				# We have to set original _MEIPASS2 value from sys._MEIPASS
				# to get --onefile mode working.
				os.putenv('_MEIPASS2', sys._MEIPASS)
			try:
				super(_Popen, self).__init__(*args, **kw)
			finally:
				if hasattr(sys, 'frozen'):
					# On some platforms (e.g. AIX) 'os.unsetenv()' is not
					# available. In those cases we cannot delete the variable
					# but only set it to the empty string. The bootloader
					# can handle this case.
					if hasattr(os, 'unsetenv'):
						os.unsetenv('_MEIPASS2')
					else:
						os.putenv('_MEIPASS2', '')

	# Second override 'Popen' class with our modified version.
	forking.Popen = _Popen
import multiprocessing
#from functools import cmp_to_key	
try:
	cmp
except NameError:
	def cmp(x, y):
		if x < y:
			return -1
		elif x > y:
		   return 1
		else:
			return 0
#----------------------------------------------------------------------
class LogStatus:
	r"""\brief Needed by the wxdemos.
	The log output is redirected to the status bar of the containing frame.
	"""

	def WriteText(self,text_string):
		self.write(text_string)

	def write(self,text_string):
		wx.GetApp().GetTopWindow().SetStatusText(text_string)

#----------------------------------------------------------------------
# The panel you want to test (TestVirtualList)
#----------------------------------------------------------------------

def cmp_to_key(mycmp):
	'Convert a cmp= function into a key= function'
	class K(object):
		def __init__(self, obj, *args):
			self.obj = obj
		def __lt__(self, other):
			return mycmp(self.obj, other.obj) < 0
		def __gt__(self, other):
			return mycmp(self.obj, other.obj) > 0
		def __eq__(self, other):
			return mycmp(self.obj, other.obj) == 0
		def __le__(self, other):
			return mycmp(self.obj, other.obj) <= 0
		def __ge__(self, other):
			return mycmp(self.obj, other.obj) >= 0
		def __ne__(self, other):
			return mycmp(self.obj, other.obj) != 0
	return K
def reverse_numeric(x, y):
	return y - x
def chunks(cur): # 65536
	global log, d
	while True:
		#log.info('Chunk size %s' %  cur.arraysize, extra=d)
		rows=cur.fetchmany()

		if not rows: break;
		yield rows	

		
class TableListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ColumnSorterMixin):
	def __init__(self, win, parent,log):
		wx.ListCtrl.__init__( self, parent, -1, style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_HRULES|wx.LC_VRULES)
		self.log=log
		self.filter_history={}
		self.current_list='TableList'
		#adding some art
		self.il = wx.ImageList(16, 16)
		a={"sm_up":"GO_UP","sm_dn":"GO_DOWN","w_idx":"WARNING","e_idx":"ERROR","i_idx":"QUESTION"}
		for k,v in a.items():
			s="self.%s= self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
			exec(s)
		self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
		#integer columns 
		#select column_id||',' from all_tab_columns where table_name='ALL_TABLES' and data_type in ('NUMBER','INTEGER');
		self.ints=[7,
		8,
		9,
		10,
		11,
		12,
		13,
		14,
		15,
		16,
		17,
		20,
		21,
		22,
		23,
		24,
		25,
		26,
		27,
		32,]
		#adding some attributes (colourful background for each item rows)
		if 1:
			self.attr1 = wx.ListItemAttr()
			self.attr1.SetBackgroundColour("yellow")
			self.attr2 = wx.ListItemAttr()
			self.attr2.SetBackgroundColour("light blue")
			self.attr3 = wx.ListItemAttr()
			self.attr3.SetBackgroundColour("purple")


		n=1
		self.itemDataMap={}
		if 1:
			self.InsertColumn(0, 'DB')
			self.InsertColumn(n+0, 'OWNER')
			self.InsertColumn(n+1, 'TABLE_NAME')
			self.InsertColumn(n+2, 'TABLESPACE_NAME')
			self.InsertColumn(n+3, 'CLUSTER_NAME')
			self.InsertColumn(n+4, 'IOT_NAME')
			self.InsertColumn(n+5, 'STATUS')
			self.InsertColumn(n+6, 'PCT_FREE')
			self.InsertColumn(n+7, 'PCT_USED')
			self.InsertColumn(n+8, 'INI_TRANS')
			self.InsertColumn(n+9, 'MAX_TRANS')
			self.InsertColumn(n+10, 'INITIAL_EXTENT')
			self.InsertColumn(n+11, 'NEXT_EXTENT')
			self.InsertColumn(n+12, 'MIN_EXTENTS')
			self.InsertColumn(n+13, 'MAX_EXTENTS')
			self.InsertColumn(n+14, 'PCT_INCREASE')
			self.InsertColumn(n+15, 'FREELISTS')
			self.InsertColumn(n+16, 'FREELIST_GROUPS')
			self.InsertColumn(n+17, 'LOGGING')
			self.InsertColumn(n+18, 'BACKED_UP')
			self.InsertColumn(n+19, 'NUM_ROWS')
			self.InsertColumn(n+20, 'BLOCKS')
			self.InsertColumn(n+21, 'EMPTY_BLOCKS')
			self.InsertColumn(n+22, 'AVG_SPACE')
			self.InsertColumn(n+23, 'CHAIN_CNT')
			self.InsertColumn(n+24, 'AVG_ROW_LEN')
			self.InsertColumn(n+25, 'AVG_SPACE_FREELIST_BLOCKS')
			self.InsertColumn(n+26, 'NUM_FREELIST_BLOCKS')
			self.InsertColumn(n+27, 'DEGREE')
			self.InsertColumn(n+28, 'INSTANCES')
			self.InsertColumn(n+29, 'CACHE')
			self.InsertColumn(n+30, 'TABLE_LOCK')
			self.InsertColumn(n+31, 'SAMPLE_SIZE')
			self.InsertColumn(n+32, 'LAST_ANALYZED')
			self.InsertColumn(n+33, 'PARTITIONED')
			self.InsertColumn(n+34, 'IOT_TYPE')
			self.InsertColumn(n+35, 'TEMPORARY')
			self.InsertColumn(n+36, 'SECONDARY')
			self.InsertColumn(n+37, 'NESTED')
			self.InsertColumn(n+38, 'BUFFER_POOL')
			self.InsertColumn(n+39, 'FLASH_CACHE')
			self.InsertColumn(n+40, 'CELL_FLASH_CACHE')
			self.InsertColumn(n+41, 'ROW_MOVEMENT')
			self.InsertColumn(n+42, 'GLOBAL_STATS')
			self.InsertColumn(n+43, 'USER_STATS')
			self.InsertColumn(n+44, 'DURATION')
			self.InsertColumn(n+45, 'SKIP_CORRUPT')
			self.InsertColumn(n+46, 'MONITORING')
			self.InsertColumn(n+47, 'CLUSTER_OWNER')
			self.InsertColumn(n+48, 'DEPENDENCIES')
			self.InsertColumn(n+49, 'COMPRESSION')
			self.InsertColumn(n+50, 'COMPRESS_FOR')
			self.InsertColumn(n+51, 'DROPPED')
			self.InsertColumn(n+52, 'READ_ONLY')
			self.InsertColumn(n+53, 'SEGMENT_CREATED')
			self.InsertColumn(n+54, 'RESULT_CACHE')
			#self.InsertColumn(2, 'Size', wx.LIST_FORMAT_RIGHT)
			#self.InsertColumn(3, 'Modified')
	 
			self.SetColumnWidth(0, 90)
			self.SetColumnWidth(n+0, 90)
			self.SetColumnWidth(n+1, 220)
			self.SetColumnWidth(n+2, 135)
			self.SetColumnWidth(n+3, 108)
			self.SetColumnWidth(n+4, 72)
			self.SetColumnWidth(n+5, 54)
			self.SetColumnWidth(n+6, 72)
			self.SetColumnWidth(n+7, 72)
			self.SetColumnWidth(n+8, 81)
			self.SetColumnWidth(n+9, 81)
			self.SetColumnWidth(n+10, 126)
			self.SetColumnWidth(n+11, 99)
			self.SetColumnWidth(n+12, 99)
			self.SetColumnWidth(n+13, 99)
			self.SetColumnWidth(n+14, 108)
			self.SetColumnWidth(n+15, 81)
			self.SetColumnWidth(n+16, 135)
			self.SetColumnWidth(n+17, 63)
			self.SetColumnWidth(n+18, 81)
			self.SetColumnWidth(n+19, 72)
			self.SetColumnWidth(n+20, 54)
			self.SetColumnWidth(n+21, 108)
			self.SetColumnWidth(n+22, 81)
			self.SetColumnWidth(n+23, 81)
			self.SetColumnWidth(n+24, 99)
			self.SetColumnWidth(n+25, 225)
			self.SetColumnWidth(n+26, 171)
			self.SetColumnWidth(n+27, 54)
			self.SetColumnWidth(n+28, 81)
			self.SetColumnWidth(n+29, 45)
			self.SetColumnWidth(n+30, 90)
			self.SetColumnWidth(n+31, 99)
			self.SetColumnWidth(n+32, 117)
			self.SetColumnWidth(n+33, 99)
			self.SetColumnWidth(n+34, 72)
			self.SetColumnWidth(n+35, 81)
			self.SetColumnWidth(n+36, 81)
			self.SetColumnWidth(n+37, 54)
			self.SetColumnWidth(n+38, 99)
			self.SetColumnWidth(n+39, 99)
			self.SetColumnWidth(n+40, 144)
			self.SetColumnWidth(n+41, 108)
			self.SetColumnWidth(n+42, 108)
			self.SetColumnWidth(n+43, 90)
			self.SetColumnWidth(n+44, 72)
			self.SetColumnWidth(n+45, 108)
			self.SetColumnWidth(n+46, 90)
			self.SetColumnWidth(n+47, 117)
			self.SetColumnWidth(n+48, 108)
			self.SetColumnWidth(n+49, 99)
			self.SetColumnWidth(n+50, 108)
			self.SetColumnWidth(n+51, 63)
			self.SetColumnWidth(n+52, 81)
			self.SetColumnWidth(n+53, 135)
			self.SetColumnWidth(n+54, 108)
	 
			j = 0
			#config=self.win.config
			
			if 1:
				connstr= 'oats/manage@jc1lbiorc7:1521/ORADB1S'
				con = cx_Oracle.connect(connstr)
				

			#cur.execute('SELECt * FROM (%s) WHERE 1=2' % q)
			sel="""
			SELECT 	USER OWNER, TABLE_NAME, TABLESPACE_NAME, CLUSTER_NAME, IOT_NAME,STATUS, PCT_FREE, PCT_USED, INI_TRANS, MAX_TRANS, INITIAL_EXTENT, NEXT_EXTENT, MIN_EXTENTS, 
					MAX_EXTENTS, PCT_INCREASE, FREELISTS, FREELIST_GROUPS, LOGGING, BACKED_UP, NUM_ROWS, BLOCKS, EMPTY_BLOCKS, AVG_SPACE, CHAIN_CNT, AVG_ROW_LEN, 
					AVG_SPACE_FREELIST_BLOCKS, NUM_FREELIST_BLOCKS, DEGREE, INSTANCES, CACHE, TABLE_LOCK, SAMPLE_SIZE, LAST_ANALYZED, PARTITIONED, IOT_TYPE, TEMPORARY, SECONDARY,
					NESTED, BUFFER_POOL, FLASH_CACHE, CELL_FLASH_CACHE, ROW_MOVEMENT, GLOBAL_STATS, USER_STATS, DURATION, SKIP_CORRUPT, MONITORING, CLUSTER_OWNER, DEPENDENCIES, 
					COMPRESSION, COMPRESS_FOR, DROPPED, READ_ONLY, SEGMENT_CREATED, RESULT_CACHE 
			FROM USER_TABLES ORDER BY 1,2"""
			cur = con.cursor()
			cur.arraysize=20
			cur.execute(sel)
			#log.info('Strating table list fetch.', extra=d)
			if 1:
				for i, chunk  in enumerate(chunks(cur)):
					for row in chunk:
						#print(len(row))
						#sys.exit()
						self.itemDataMap[i]=['ORADB1S']+[self.nvl(x,i) for i,x in enumerate(row)]
			if 0:
				for i, chunk  in enumerate(chunks(cur)):
					for row in chunk:
						#print(row)
						self.itemDataMap[i]=row
						#self.InsertItem(j, 'ORADB1S')
						self.InsertItem(j, row[0])
						for c,col in enumerate(row):
							if not col: col=''
							#print (col)
							if c>0:
								self.SetItem(j, c+n, str(col))

						if True:
							self.SetItemImage(j, 1)
						elif ex == 'py':
							self.SetItemImage(j, 2)
						elif ex == 'jpg':
							self.SetItemImage(j, 3)
						elif ex == 'pdf':
							self.SetItemImage(j, 4)
						else:
							self.SetItemImage(j, 0)
			 
						if (j % 2) == 0:
							self.SetItemBackgroundColour(j, '#e6f1f5')
						j = j + 1
					
		#These two should probably be passed to init more cleanly
		#setting the numbers of items = number of elements in the dictionary
		#self.itemDataMap = musicdata
		self.itemIndexMap = self.itemDataMap.keys()
		#print(self.itemIndexMap )
		self.SetItemCount(len(self.itemDataMap))
		self.data={}
		self.data[self.current_list]= self.itemDataMap
		#print (self.itemDataMap)
		#mixins
		#listmix.ListCtrlAutoWidthMixin.__init__(self)
		#listmix.ColumnSorterMixin.__init__(self, 55)
		self.setMixins()
		self.col_id=1
		#sort by genre (column 2), A->Z ascending order (1)
		self.if_reverse=True
		self.SortListItems(self.col_id, 1)
		
		#events
		self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
		self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)
		self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
	def setMixins (self):
		self.SetItemCount(len(self.itemIndexMap))
		listmix.ListCtrlAutoWidthMixin.__init__(self)
		listmix.ColumnSorterMixin.__init__(self, 55)
	def set_data(self):
		#print 'set_data'
		flist=OrderedDict()
		i=0  
		os.chdir(self.save_to_dir)
		#print filter(os.path.isfile,os.listdir(self.save_to_dir))
		#print os.listdir(self.save_to_dir)
		#e(0)
		#print 'dir'
		#pprint(filter(os.path.isfile,os.listdir(self.save_to_dir)))
		
		
		for f in filter(os.path.isfile,os.listdir(self.save_to_dir)):
			#print f
			d= datetime.datetime.fromtimestamp(os.path.getmtime(f))
			dt= d.strftime('%Y-%m-%d %H:%M:%S')
			cv, tmpl,name= f.split(';')
			name=name.split('.')[0]
			#print name
			type='Copy'
			if tmpl.startswith('CSV'):
				type='Load'
			if '.CSV_' in tmpl:
				type='Spool'
			flist[i] = [name.strip(' '),dt,tmpl.split('.')[1],cv.split('.')[0],cv.split('.')[1],type,tmpl.split('.')[0],self.save_to_dir,f]
			i +=1
		#pprint(flist)
		self.data[self.current_list]= flist
		self.parent.itemDataMap=self.data[self.current_list]		
	def get_second_elem(self,iterable):
		#global b
		return self.sub(iterable[1], self.col_id)
	def nvl(self,val, col_id):
		if val: return val
		else: 
			return ''
	def sub(self, val, col_id):
		if val: return val
		else: 	
			if col_id in self.ints:
				return -1
			else:
				return ''
	def OnColClick(self,evt):
		#print(1)
		#self.Sort()
		#print (dir(evt))
		colid=evt.GetColumn()
		if colid == self.col_id:
			self.if_reverse=not self.if_reverse
		else:
			self.if_reverse=False
		self.col_id=colid
		print (self.col_id, self.col_id in self.ints)
		evt.Skip()

	def OnItemSelected(self, event):
		self.currentItem = event.m_itemIndex
		self.log.WriteText('OnItemSelected: "%s", "%s", "%s", "%s"\n' %
						   (self.currentItem,
							self.GetItemText(self.currentItem),
							self.getColumnText(self.currentItem, 1),
							self.getColumnText(self.currentItem, 2)))

	def OnItemActivated(self, event):
		self.currentItem = event.m_itemIndex
		self.log.WriteText("OnItemActivated: %s\nTopItem: %s\n" %
						   (self.GetItemText(self.currentItem), self.GetTopItem()))

	def getColumnText(self, index, col):
		item = self.GetItem(index, col)
		return item.GetText()

	def OnItemDeselected(self, evt):
		self.log.WriteText("OnItemDeselected: %s" % evt.m_itemIndex)


	#---------------------------------------------------
	# These methods are callbacks for implementing the
	# "virtualness" of the list...


	def OnGetItemText(self, item, col):
		#print(item)
		index=list(self.itemIndexMap)[item]
		s = self.itemDataMap[index][col]
		return str(s)
	def OnGetItemImage(self, item):
		index=list(self.itemIndexMap)[item]
		genre=self.itemDataMap[index][2]

		if genre=="Rock":
			return self.w_idx
		elif genre=="Jazz":
			return self.e_idx
		elif genre=="New Age":
			return self.i_idx
		else:
			return -1

	def OnGetItemAttr(self, item):
		#return self.attr2
		index=list(self.itemIndexMap)[item]
		genre=self.itemDataMap[index][2]

		if genre=="Rock":
			return self.attr2
		elif genre=="Jazz":
			return self.attr1
		elif genre=="New Age":
			return self.attr3
		else:
			return None

	#---------------------------------------------------
	# Matt C, 2006/02/22
	# Here's a better SortItems() method --
	# the ColumnSorterMixin.__ColumnSorter() method already handles the ascending/descending,
	# and it knows to sort on another column if the chosen columns have the same value.
	def Sort(self):
		import operator
		#self.SortListItems(1,1)
		items=[(x,v[self.col_id]) for x,v in self.itemDataMap.items()]
		sorted_x = sorted(items, key=operator.itemgetter(1), reverse=self.if_reverse)
		#pprint(sorted_x)
		self.Refresh()
	def SortItems(self,sorter=cmp):
		import operator
		#pass
		#items = list(self.itemDataMap.keys())
		#items.sort(sorter)
		#items= sorted(items, key=cmp_to_key(cmp)) 
		#self.itemIndexMap = items
		
		# redraw the list
		#self.SortListItems(2,1)
		#print (self.col_id)
		items=[(x,v[self.col_id]) for x,v in self.itemDataMap.items()]
		#pprint(items)
		
		sorted_x = sorted(items, key=self.get_second_elem, reverse=self.if_reverse)
		#pprint(sorted_x)
		self.itemIndexMap=[x[0] for x in sorted_x]
		
		if 0:
			self.itemIndexMap=[x[0] for x in sorted(self.itemDataMap.items(), key=operator.itemgetter(self.col_id-1), reverse= self.if_reverse)]
			pprint(sorted(self.itemDataMap.items(), key=operator.itemgetter(self.col_id-1), reverse= self.if_reverse))
			print([x[0] for x in sorted(self.itemDataMap.items(), key=operator.itemgetter(self.col_id-1), reverse= self.if_reverse)])
			pprint([self.itemDataMap[x][self.col_id] for x in [x[0] for x in sorted(self.itemDataMap.items(), key=operator.itemgetter(1,self.col_id), reverse= self.if_reverse)]])
		self.Refresh()


	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def SortListItems(self, col=-1, ascending=1):
		pass	
	def GetListCtrl(self):
		return self

	# Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
	def GetSortImages(self):
		return (self.sm_dn, self.sm_up)

	#XXX Looks okay to remove this one (was present in the original demo)
	#def getColumnText(self, index, col):
	#    item = self.GetItem(index, col)
	#    return item.GetText()
	def get_source_db_connect_string(self,cfg, spool_spec):
		global JOB_NAME
		assert 'connectors' in cfg.keys(), "'connectors' section is missing in config."
		assert 'from' in spool_spec.keys(), "'from' definition is missing in spool specification."
		assert spool_spec['from'] in cfg['connectors'].keys(), 'database "%s" is missing in "connectors" configuration.' % spool_spec['from']
		cli_var_name='%s0%s0%s' % (JOB_NAME,'connectors', spool_spec['from'])

		assert cli_var_name.upper() in [x.upper() for x in os.environ.keys()] , 'Source db password is not set.\nUse "set %s=<passwd>".' % cli_var_name
		conn = cfg['connectors'][spool_spec['from']].split('@')
		assert len(conn)==2, 'Wrong connector format. Should be "user@dbserver/SID"'
		pwd=os.environ[cli_var_name]
		
		return  ('/%s@' % pwd). join (conn)	

		

class TableSpooler:
	def __init__(self, win, table_list, out_dir, log):
		self.win = win
		#print ('Frame:',self.win)
		#e(0)
		self.table_list = table_list
		self.out_dir = out_dir
		self.log=log

	def Start(self):
		self.keepGoing = self.running = True
		_thread.start_new_thread(self.Run, ())

	def Stop(self):
		self.keepGoing = False

	def IsRunning(self):
		return self.running

	def Run(self):
		self.ExtractData()
		if 0:
			while self.keepGoing:
				# We communicate with the UI by sending events to it. There can be
				# no manipulation of UI objects from the worker thread.
				evt = UpdateBarEvent(barNum = 1, value = 1)
				wx.PostEvent(self.win, evt)

				#time.sleep(1)

		self.running = False
	def i(self,msg):
		global d
		self.log.info(msg, extra=d)	
	def get_nls_params(self, cfg, spool_spec):
		#pprint(cfg)
		#e(0)
		assert 'nls_param_sets' in cfg.keys(), "'nls_param_sets' section is missing in config."
		assert 'nls_params' in spool_spec.keys(), "'nls_params' definition is missing in spool specification."
		assert spool_spec['nls_params'] in cfg['nls_param_sets'].keys(), 'nls_param_set "%s" is missing in nls_param_sets configuration.' % spool_spec['nls_params']
		return cfg['nls_param_sets'][spool_spec['nls_params']]





	def get_source_db_connect_string(self,cfg, spool_spec):
		global JOB_NAME
		assert 'connectors' in cfg.keys(), "'connectors' section is missing in config."
		assert 'from' in spool_spec.keys(), "'from' definition is missing in spool specification."
		assert spool_spec['from'] in cfg['connectors'].keys(), 'database "%s" is missing in "connectors" configuration.' % spool_spec['from']
		cli_var_name='%s0%s0%s' % (JOB_NAME,'connectors', spool_spec['from'])

		assert cli_var_name.upper() in [x.upper() for x in os.environ.keys()] , 'Source db password is not set.\nUse "set %s=<passwd>".' % cli_var_name
		conn = cfg['connectors'][spool_spec['from']].split('@')
		assert len(conn)==2, 'Wrong connector format. Should be "user@dbserver/SID"'
		pwd=os.environ[cli_var_name]
		
		return  ('/%s@' % pwd). join (conn)			
	def ExtractData(self):
		global pool_size, config
		self.i('start')


		queries=[]



		#__builtin__.trd_date = None
				
		#pprint (table_list)
		#e(0)
		assert self.out_dir, 'out_dir is not set'
		for k,v in enumerate(self.table_list):
			db, schema, table= v
			#print(db, schema, table)
			if db and  schema and table:
				q= "SELECT * FROM %s.%s" % (schema, table);
				#q= v['query'].strip().strip('/').strip(';').strip()
				
				fn=os.path.join(self.out_dir,'%s.%s.%s.csv' % ( db, schema, table))
				#delete file if exists
				#next step wait for IN_CREATE event for ts_out_dir
				if os.path.isfile(fn): 
					try:
						unlink(fn)
					except Exception as err:
						tb = traceback.format_exc()
						#print (tb)
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]				
						log.error('%s %s %s' % (exc_type, fname, exc_tb.tb_lineno), extra=d)
						raise
				nls=self.get_nls_params(config.cfg,config.cfg['profile']['default'])
				#get password from environment
				conn = self.get_source_db_connect_string(config.cfg,config.cfg['profile']['default'])
				#print (fn)
				queries.append([conn,fn,q,nls])
			else:
				log.error('Table name is not set: %s, %s, %s' % (db, schema, table), extra=d)
		#e(0)
		#e(0)
		if len(queries):
			m= multiprocessing.Manager()
			if pool_size>len(queries):
				pool_size=len(queries)
			inputs = list([(i,q, opt) for i,q in enumerate(queries)])
			
			#pprint(inputs)
			#e(0)
			#import re
			#print(re.escape(inputs[0][1][0]))
			#e(0)
			pool_size = multiprocessing.cpu_count()*2-2
			self.pool = m.Pool(processes=pool_size,
										initializer=start_process,
										)
			pool_outputs = self.pool.map(extract_query_data, inputs)
			self.pool.close() # no more tasks
			self.pool.join()  # wrap up current tasks

			#print ('Pool    :', pool_outputs)
			#e(0)
			print  ('Total rows extracted    : %d' % sum([r[0] for r in pool_outputs]))
			job_status={'spool_status':[r[2] for r in pool_outputs],'spool_files':[r[1] for r in pool_outputs]}
			print ('-'*60)
			for r in pool_outputs:
				log.info('Status: %s' % (r[2]),extra=d)
			for r in pool_outputs:
				print('%s' % (r[1]))
			print ('-'*60)
		else:		
			log.error('Table list is empty',extra=d)

def import_module(filepath):
	class_inst = None
	mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
	assert os.path.isfile(filepath), 'File %s does not exists.' % filepath
	if file_ext.lower() == '.py':
		py_mod = imp.load_source(mod_name, filepath)

	elif file_ext.lower() == '.pyc':
		py_mod = imp.load_compiled(mod_name, filepath)
	return py_mod
def open_settings(filename):
	conf = wx.FileConfig(localFilename = filename)
	def create_entry(entry_name, entry_value):
		if not conf.HasEntry(entry_name):
			if isinstance(entry_value, (str, bytes)):
				conf.Write(entry_name, entry_value)
			elif isinstance(entry_value, int):
				conf.WriteInt(entry_name, entry_value)
			elif isinstance(entry_value, bool):
				conf.WriteBool(entry_name, entry_value)
			else:
				conf.Write(entry_name, repr(entry_value))
			return True
		else:
			return False
	flag_flush = False
	if create_entry('Language/Catalog', getdefaultlocale()[0]):
		flag_flush = True
	if create_entry('GUI/load_default_perspective_on_start', True):
		flag_flush = True
	if create_entry('GUI/save_default_perspective_on_exit', True):
		flag_flush = True
	if create_entry('GUI/perspective', ''):
		flag_flush = True
	if create_entry('GUI/load_default_state_on_start', True):
		flag_flush = True
	if create_entry('GUI/save_default_state_on_exit', True):
		flag_flush = True
	if create_entry('GUI/fullscreen_style', default_fullscreen_style):
		flag_flush = True
	if create_entry('GUI/centre_on_screen', repr((False, wx.BOTH))):
		flag_flush = True
	if create_entry('GUI/default_open_path', '.'):
		flag_flush = True
	if flag_flush:
		conf.Flush()
	return conf	
def chunks(cur): # 65536
	global log, d
	while True:
		#log.info('Chunk size %s' %  cur.arraysize, extra=d)
		rows=cur.fetchmany()

		if not rows: break;
		yield rows

		
#----------------------------------------------------------------------
# The main window
#----------------------------------------------------------------------
# This is where you populate the frame with a panel from the demo.
#  original line in runTest (in the demo source):
#    win = TestPanel(nb, log)
#  this is changed to:
#    self.win=TestPanel(self,log)
#----------------------------------------------------------------------
def start_process():
	global log
	log.info('Starting ' + multiprocessing.current_process().name, extra=d)	
	
def extract_query_data(data):
	global log, d
	#d = {'iteration': 0,'pid':os.getpid(), 'rows':0}
	id, query, opt=data	
	status=1
	conn,fn,q, nls  = query
	#evt = UpdateBarEvent(barNum = 1, value = 1)
	#wx.PostEvent(win, evt)
	try:
		#print(conn)
		con = cx_Oracle.connect(conn)
		log.info('Connected.', extra=d)
		cur = con.cursor()
		nls_cmd="ALTER SESSION SET %s" % ' '.join(nls.split())
		cur.execute(nls_cmd)
		#print ('SELECt * FROM (%s) WHERE 1=2' % q)
		cur.execute('SELECt * FROM (%s) WHERE 1=2' % q)
		
		sel= 'SELECT "' + ("\"||'%s'||\"" % opt.column_delimiter[0]). join([k[0] for k in cur.description]) + '" data   FROM ( %s)' % q 
		
		header = opt.column_delimiter[0].join([k[0] for k in cur.description])
		cur.arraysize=opt.array_size
		cur.execute(sel)
		#print('done')
		cnt=0
		
		
		if opt.compress:
			fn='%s.gz' % fn
			with gzip.open(fn, 'wb') as f_out:	
				log.info('Strating data extract.', extra=d)
				for i, chunk  in enumerate(chunks(cur)):
					d['iteration']=i
					cnt+=len(chunk)
					d['rows']=cnt
					try:
						
						#log.info('Starting ' + multiprocessing.current_process().name, extra=d)
						f_out.write('\n'.join([row[0] for row in chunk]))
						f_out.write('\n')
						log.info('extracted into %s' % os.path.basename(fn), extra=d )

					except Exception as err:
						tb = traceback.format_exc()
						#print (tb)
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						#print(exc_type, fname, exc_tb.tb_lineno)
						raise
		else:	
			with open(fn, 'wb') as fh:
				fh.seek(0)
				#print (header)
				fh.write (header.encode('utf-16'))
				for i, chunk  in enumerate(chunks(cur)):
					d['iteration']=i
					cnt+=len(chunk)
					d['rows']=cnt
					fh.write(('\n'.join([row[0] for row in chunk])).encode('utf-16'))
					fh.write('\n'.encode('utf-16'))
					#log.info('%d rows added to %s' % (cnt,os.path.basename(fn)), extra=d )
					log.info('%d rows extracted' % cnt, extra=d )
				log.info('Finished extract.', extra=d)
		status=0
		
		cur.close()
		con.close()
		
	except  Exception as err:
		#import pickle
		#pickled = pickle.dumps(err)
		#pickle.loads(pickled) 
		err=str(err)
		exc, er, traceback = sys.exc_info()
		print ('#'*50)
		print ('#'*20, 'EXCEPTION', '#'*19)
		print ('#'*50)
		print(exc, traceback.tb_frame.f_code.co_filename,traceback.tb_lineno, er)
		print(err)
		print ('#'*50)
		print ('#'*50)
		print ('#'*50)
		(cnt, fn, status) = (-1,-1,-1)
			
		
		#print (exc, traceback.tb_frame.f_code.co_filename, 'ERROR ON LINE', traceback.tb_lineno, '\n', err)
		#estr= '|'.join([exc, traceback.tb_frame.f_code.co_filename, 'ERROR ON LINE', traceback.tb_lineno, er])
		#log.error(estr, extra=d) 
	log.info('Done.' , extra=d)		
	return [cnt, fn, status]

def unlink(dirname):
	if (os.name == "posix"):
		os.unlink(dirname)
	elif (os.name == "nt"):
		#shutil.rmtree( os.path.dirname(dirname) )
		os.remove(dirname)
	else:
		log.error('Cannot unlink. Unknown OS.', extra=d)	

def delete_file(filename):
	if (os.name == "posix"):
		os.unlink(filename)
	elif (os.name == "nt"):
		#shutil.rmtree( os.path.dirname(dirname) )
		os.remove(filename)
	else:
		log.error('Cannot unlink. Unknown OS.', extra=d)		
class ListCtrlPanel(wx.Panel):
	def __init__(self, *args ):
		self.ID=wx.NewId()
		wx.Panel.__init__(self,*args, style=wx.WANTS_CHARS)
		self.list=None
		self.itemDataMap={}
		self.itemIndexMap = []
	#def setColSorter(self):
	def GetListCtrl(self):
		return self.list
	def SetListCtrl(self, list):
		self.list=list
		listmix.ColumnSorterMixin.__init__(self,self.list.GetColumnCount())
		
		
class TableHunter(wx.Frame):
	#----------------------------------------------------------------------
	def __init__(self, *args, **kwargs):
		wx.Frame.__init__(self,  *args)
		import gettext
		_ = gettext.gettext
		panel = wx.Panel(self)
		self.app = kwargs.pop('app', None)
		self.log = kwargs.pop('log', None)
		self.ts_out_dir = kwargs.pop('ts_out_dir', None)
		self.config = kwargs.pop('config', None)	
		self.pos=[(0,0)]		
		self.table_list = table_list= TableListCtrl(self, panel, self.log)
		#panel.SetListCtrl(table_list)
		self.filter_history={}
		table_list.Bind(wx.EVT_LIST_BEGIN_DRAG, self.onDrag)
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		
		self.filter =self.getFilter(panel,self.table_list)
		
		self.currentItem = 0
		navig = wx.BoxSizer(wx.HORIZONTAL)
		
		sizer.Add((5,5))  # Make sure there is room for the focus ring
		navig.Add(self.filter, 0, wx.LEFT|wx.BOTTOM)
		imageFile = os.path.join(home,'images','exec.png')
		image1 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()		
		self.btn_refresh=wx.BitmapButton(panel, id=-1, bitmap=image1,size = (image1.GetWidth()+6, image1.GetHeight()+6))
		self.gen_bind(wx.EVT_BUTTON,self.btn_refresh, self.OnBtnRefreshList,(self.pos))
		navig.Add(self.btn_refresh, 0, wx.LEFT)
		sizer.Add(navig, 0, wx.EXPAND)
		sizer.Add(table_list, 1, wx.EXPAND)
		panel.SetSizer(sizer)
		
		self.pane_captions ={}
		self.pane_captions_0={
							'main_toolbar':('main_toolbar', _('main toolbar')),
							'svg_panel':('svg_panel', _('svg panel')),
							'app_log_ctrl':('log', _('log')),
							'shell':('shell', _('shell'))
							}		
		if 1:
			self.Bind(wx.EVT_CLOSE, self.OnClose) 
			

		if 1:
			if self.app.settings.ReadBool('GUI/load_default_state_on_start', True):
				self.method_load_default_state()

			self.default_open_path = self.app.settings.Read('GUI/default_open_path', os.getcwd())
		#self.spooler=TableSpooler( win=self, log=self.log, ts_out_dir=self.ts_out_dir)	
		self.aui_manager = AuiManager()	
		self.aui_manager.SetManagedWindow(self)
		#self.Bind(EVT_UPDATE_BARGRAPH, self.OnUpdate)

		self.threads = []

		self.Center()
		self.Show(True)
	def gen_bind(self, type, instance, handler, *args, **kwargs):
		self.Bind(type, lambda event: handler(event, *args, **kwargs), instance)		
	def OnBtnRefreshList(self, event, params):
		print ('OnBtnRefreshList')
		self.table_list.set_data()
		self.RecreateList(None,(self.list,self.filter))		
	def getFilter(self,parent,list):
		#self.treeMap[ttitle] = {}
		self.searchItems={}
		#print _tP
		#tree = TacoTree(parent,images,_tP)
		filter = wx.SearchCtrl(parent, style=wx.TE_PROCESS_ENTER, size=(380,35))
		#text = wx.StaticText(panel, -1, 'my text', (20, 100))
		font = wx.Font(14, wx.DECORATIVE, wx.NORMAL,wx.NORMAL ) # wx.FONTWEIGHT_BOLD)
		filter.SetFont(font)
		#filter.ShowSearchButton( True )
		filter.ShowCancelButton(True)
		#filter.Bind(wx.EVT_TEXT, self.RecreateTree)
		self.gen_bind(wx.EVT_TEXT,filter, self.RecreateList,(list,filter))
		#filter.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnSearchCancelBtn)
		self.gen_bind(wx.EVT_SEARCHCTRL_CANCEL_BTN,filter, self.OnSearchCancelBtn,(list, filter))
		self.gen_bind(wx.EVT_TEXT_ENTER,filter, self.OnSearch,(list, filter))
		searchMenu = wx.Menu()
		item = searchMenu.AppendRadioItem(-1, "All")
		#self.Bind(wx.EVT_MENU, self.OnSearchMenu, item)
		self.gen_bind(wx.EVT_MENU, item,self.OnSearchMenu,(list, filter))

		item = searchMenu.AppendRadioItem(-1, "Tables")
		#self.Bind(wx.EVT_MENU, self.OnSearchMenu, item)
		self.gen_bind(wx.EVT_MENU, item,self.OnSearchMenu,(list, filter))
		item = searchMenu.AppendRadioItem(-1, "Views")
		#self.Bind(wx.EVT_MENU, self.OnSearchMenu, item)
		self.gen_bind(wx.EVT_MENU, item,self.OnSearchMenu,(list, filter))
		if 0:
			item = searchMenu.AppendRadioItem(-1, "Files")
			#self.Bind(wx.EVT_MENU, self.OnSearchMenu, item)
			self.gen_bind(wx.EVT_MENU, item,self.OnSearchMenu,(list, filter))
		
		filter.SetMenu(searchMenu)		


		#self.RecreateTree(None, (tree, filter,ttitle,_tP,_tL))
		#tree.SetExpansionState(self.expansionState)
		#tree.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded)
		#self.gen_bind(wx.EVT_TREE_ITEM_EXPANDED, tree, self.OnItemExpanded,(tree))
		#tree.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed)
		#self.gen_bind(wx.EVT_TREE_ITEM_COLLAPSED,tree, self.OnItemCollapsed,(tree))
		#tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
		#self.gen_bind(wx.EVT_TREE_SEL_CHANGED, tree,self.OnSelChanged,(tree,filter,ttitle))
		#tree.Bind(wx.EVT_LEFT_DOWN, self.OnTreeLeftDown)
		#self.gen_bind(wx.EVT_LEFT_DOWN, tree,self.OnTreeLeftDown, (ttitle) )
		#self.BuildMenuBar(_tL,ttitle)
		return filter	
	def RecreateList(self, evt=None, tf=None):
		# Catch the search type (name or content)
		#cl =self.list.current_list
		#print '############# in RecreateList', self.pos,'cl:', cl
		(list, filter) = tf
		fltr = filter.GetValue()
		favs={}
		#print fltr
		#print self.list.current_list, 1
		#btns=self.list.nav_list[self.list.current_list]['hot_keys']
		#Publisher().sendMessage( "set_buttons", (self.list.pos,btns) )
		if 1:
			searchMenu = filter.GetMenu().GetMenuItems()
			fullSearch = searchMenu[1].IsChecked()
			searchItems=self.searchItems
			if evt:
				#print(dir(evt.ClassName))
				#print (evt.ClassName, evt.Id, evt.GetEventType())
				#e(0)
				if fullSearch:
					#print 'RecreateList/fullSearch'
					#Publisher().sendMessage( "force_search", (self.pos,fltr) )
					send("force_search", (self.pos,fltr))
					# Do not`scan all the demo files for every char
					# the user input, use wx.EVT_TEXT_ENTER instead
					#return

			#expansionState = list.GetExpansionState()

			current = None
			#print(dir(list))
			#print list.GetSelectedItemCount()
			if 0:
				item = list.GetSelection()
				if item:
					prnt = list.GetItemParent(item)
					if prnt:
						current = (list.GetItemText(item),
								   list.GetItemText(prnt))
						
			#list.Freeze()
			
			#self.root = list.AddRoot(activeProjName)
			#list.SetItemImage(self.root, 0)
			#list.SetItemPyData(self.root, 0)

			treeFont = list.GetFont()
			catFont = list.GetFont()

			# The old native treectrl on MSW has a bug where it doesn't
			# draw all of the text for an item if the font is larger than
			# the default.  It seems to be clipping the item's label as if
			# it was the size of the same label in the default font.
			if 'wxMSW' not in wx.PlatformInfo or wx.GetApp().GetComCtl32Version() >= 600:
				treeFont.SetPointSize(treeFont.GetPointSize()+2)
				treeFont.SetWeight(wx.BOLD)
				catFont.SetWeight(wx.BOLD)
				
			#list.SetItemFont(self.root, treeFont)
			
			firstChild = None
			selectItem = None
			
			count = 0
			
			#for key, items in list.data.items():
			#items=list.data.values()
			if fltr:
				 self.filter_history[list.current_list]=fltr

			item_mask='%s'
			#print 'RecreateList'
			#print list.data[list.current_list]
			print ('',fltr.lower())
			if 1:
				count += 1
				if fltr:
					keys = [key for key,item in list.data[list.current_list].items() if fltr.lower() in str(item[2]).lower()]
				else:
					keys = [key for key,item in list.data[list.current_list].items()]
				#print keys
				#print list.data[list.current_list].items()
				list.DeleteAllItems()
				#print ('len keys',len(keys))
				#pprint(keys)
				#e(0)
				self.table_list.itemIndexMap = keys
				if keys:
					self.table_list.setMixins()
					self.table_list.Refresh()
				if 0 and keys:
					#print keys
					j=0
					
					#pprint(list.data[list.current_list])
					for key in keys:
						#print 'key',key
						
						i= list.data[list.current_list][key]
						#print 'i',i
						#e(0)
						list.Refresh()
						if  0:
							index=list.InsertStringItem(sys.maxsize, item_mask % i[0])
							for idx in range(1,len(i)-2):
								#print 'idx', idx
								#print i[idx]
								list.SetStringItem(index, idx, str(i[idx]))


							list.SetItemData(index,key)
							
							keycolid=0
							if favs.has_key(i[keycolid]):
								item = list.GetItem(index)
								font = item.GetFont()
								font.SetWeight(wx.FONTWEIGHT_BOLD)
								item.SetFont(font)
								# This does the trick:
								list.SetItem(item)
							

							#if i[1] == 'xml':
							#print list._imgstart,list.img_offset
							imgs= { 'default':'images/database_green_16.png', 
									'DEV':'images/database_green_16.png',
									'PROD':'images/database_red_16.png',
									'UAT':'images/database_blue_16.png',
									'QA':'images/database_black_16.png'}
							imgs={k:os.path.join(home,v) for k,v in imgs.items()}
							img_type_col_id= self.list.img_col
							img_type = i[img_type_col_id]
							img_name=None
							if imgs.has_key(img_type):
								img_name=imgs[img_type]
							else:
								img_name=imgs['default']
							#print img_name
							img_id=self.list.image_refs[img_name]
							list.img[key]=img_id
							list.SetItemImage(index, list.img[key])
							#print 'SetItemImage',index,key,list.img[key]
							if 0:
								if (j % 2) == 0:
									list._bg='#e6f1f5'
									list.SetItemBackgroundColour(index, list._bg)
							j += 1				
					if 0:
						child = list.AppendItem(self.root, category, image=count)
						list.SetItemFont(child, catFont)
						list.SetItemPyData(child, count)
						if not firstChild: firstChild = child
						for childItem in items:
							image = count
							if DoesModifiedExist(childItem):
								image = len(_tP)
							theDemo = list.AppendItem(child, childItem, image=image)
							list.SetItemPyData(theDemo, count)
							self.treeMap[ttitle][childItem] = theDemo
							#if current and (childItem, category) == current:
							#	selectItem = theDemo
							
						

			#print 'list.Thaw()'
			#print (dir(list))
			#print list.pos

			searchItems = {}		
			#listmix.ColumnSorterMixin.__init__(self, self.table_list.GetColumnCount())
			#listmix.ColumnSorterMixin.__init__(self.table_list, 55)
			out=''
			max_len=15
			dots=''
			#if not out:
			#out =self.root_status
			#sb=self.status
			if 0: #not sb:
				sb=cl
				if not sb:
					sb='Double click on pipeline file.'

			#send( "update_status_bar", (sb,self.pos))	
	def OnSearchCancelBtn(self, event,tf):
		(list, filter) = tf
		self.filter.SetValue('')
		self.filter_history[list.current_list]=''
		self.OnSearch(event,tf)	
	def OnSearch(self, event, tf):
		#search in every list
		
		(list, filter) = tf
		fltr = filter.GetValue()
		#print 'OnSearch',fltr, self.searchItems
		self.filter_history[list.current_list]=fltr
		searchItems=self.searchItems
		if not fltr:
			self.RecreateList(None,(list, filter))
			return

		wx.BeginBusyCursor()		
	
		#searchItems=[item for item in list.data.values() if fltr.lower() in str(item[0]).lower()]
	
		self.RecreateList(None,(list, filter)) 
		wx.EndBusyCursor()	
	def OnSearchMenu(self, event, tparams):
		(tree, filter)=tparams
		# Catch the search type (name or content)
		searchMenu = filter.GetMenu().GetMenuItems()
		fullSearch = searchMenu[1].IsChecked()
		fltr=filter.GetValue()
		if 1:
			if fullSearch:
				#print 'OnSearchMenu/fullSearch'
				#Publisher().sendMessage( "force_search", (self.pos,fltr) )
				send("force_search", (self.pos,fltr) )
				self.OnSearch(None,tparams)
			else:
				self.RecreateList(None,tparams)		
	def OnUpdate(self, evt):
		print('@'*20)
		print('@'*20)
		print ('update', os.getpid)
		print('@'*20)
		print('@'*20)
	
	def onDrag0(self, event):
		""""""
		data = wx.FileDataObject()
		obj = event.GetEventObject()
		id = event.GetIndex()
		filename = obj.GetItem(id).GetText()
		dirname = os.path.dirname(os.path.abspath(os.listdir(".")[0]))
		fullpath = str(os.path.join(dirname, filename))

		data.AddFile(fullpath)
 
		dropSource = wx.DropSource(obj)
		dropSource.SetData(data)
		#result = dropSource.DoDragDrop()
		result =  dropSource.DoDragDrop(wx.Drag_AllowMove) 
		#print (fullpath)
		#print(result)
	def method_save_default_perspective(self):
		self.method_set_default_pane_captions()
		current_perspective = self.aui_manager.SavePerspective()
		self.method_set_translation_pane_captions()
		if self.app.settings.Read('GUI/perspective', '') != current_perspective:
			self.app.settings.Write('GUI/perspective', current_perspective)
			self.app.settings.Flush()
	def method_set_default_pane_captions(self):
		for name, caption in self.pane_captions.items():
			self.aui_manager.GetPane(name).Caption(caption[0])

	def method_set_translation_pane_captions(self):
		for name, caption in self.pane_captions.items():
			self.aui_manager.GetPane(name).Caption(caption[1])			
	def method_save_default_state(self):
		flag_flush = False
		position = self.GetPosition()
		if position != eval(self.app.settings.Read('GUI/position', '()')):
			self.app.settings.Write('GUI/position', repr(position))
			flag_flush = True
		size = self.GetSize()
		if size != eval(self.app.settings.Read('GUI/size', '()')):
			self.app.settings.Write('GUI/size', repr(size))
			flag_flush = True
		font = self.GetFont().GetNativeFontInfo().ToString()
		if font != self.app.settings.Read('GUI/font', ''):
			self.app.settings.Write('GUI/font', font)
			flag_flush = True
		is_maximized = self.IsMaximized()
		if is_maximized != self.app.settings.ReadBool('GUI/maximized', False):
			self.app.settings.WriteBool('GUI/maximized', is_maximized)
			flag_flush = True
		is_iconized = self.IsIconized()
		if is_iconized != self.app.settings.ReadBool('GUI/iconized', False):
			self.app.settings.WriteBool('GUI/iconized', is_iconized)
			flag_flush = True
		is_fullscreen = self.IsFullScreen()
		if is_fullscreen != self.app.settings.ReadBool('GUI/fullscreen', False):
			self.app.settings.WriteBool('GUI/fullscreen', is_fullscreen)
			flag_flush = True
		if flag_flush:
			self.app.settings.Flush()
	def method_load_default_state(self):
		#frame_font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
		#frame_font.SetNativeFontInfoFromString(self.app.settings.Read('GUI/font', ''))
		#self.SetFont(frame_font)
		self.SetSize(eval(self.app.settings.Read('GUI/size', '(100,100)')))
		self.SetPosition(eval(self.app.settings.Read('GUI/position', '(100,100)')))
		centre_on_screen = eval(self.app.settings.Read('GUI/centre_on_screen', repr((False, wx.BOTH))))
		if centre_on_screen[0]:
			self.CentreOnScreen(centre_on_screen[1])
		self.Maximize(self.app.settings.ReadBool('GUI/maximized', False))
		self.Iconize(self.app.settings.ReadBool('GUI/iconized', False))
		self.ShowFullScreen(self.app.settings.ReadBool('GUI/fullscreen', False), self.app.settings.ReadInt('GUI/fullscreen_style', default_fullscreen_style))
		
	def _Exit(self):
		if self.app.settings.ReadBool('GUI/save_default_state_on_exit', True):
			self.method_save_default_state()
		if False or self.app.settings.ReadBool('GUI/save_default_perspective_on_exit', True):
			self.method_save_default_perspective()
		#self.main_toolbar.Destroy()		
		self.aui_manager.UnInit()
		self._StopThreads()
		self.Destroy()			
	def OnClose(self, event):
		#self.ticker.Stop()
		self._Exit()
		event.Skip()
	def _StopThreads(self):
		busy = wx.BusyInfo("One moment please, waiting for threads to die...")
		wx.Yield()

		for t in self.threads:
			t.Stop()

		running = 1

		while running:
			running = 0

			for t in self.threads:
				running = running + t.IsRunning()

			time.sleep(0.1)

		#self.Destroy()
		
	#----------------------------------------------------------------------
	def get_selected_items(self):
		"""
		Gets the selected items for the list control.
		Selection is returned as a list of selected indices,
		low to high.
		"""
		selection = []

		# start at -1 to get the first selected item
		current = -1
		while True:
			next = self.table_list.GetNextItem(current, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if next == -1:
				return selection

			selection.append(next)
			current = next
		return selection

	def GetNextSelected(self, current):
		"""Returns next selected item, or -1 when no more"""

		return self.table_list.GetNextItem(current, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
							
	def onDrag(self, event):
		data = wx.FileDataObject()
		obj = event.GetEventObject()
		dropSource = wx.DropSource(obj)
		id = event.GetIndex()
		#print(id)
		db, schemaname, tablename= obj.GetItem(id,0).GetText(), obj.GetItem(id,1).GetText(), obj.GetItem(id,2).GetText()
		print (schemaname, tablename)
		
		items=self.get_selected_items()
		#print(len(items))
		tl=self.table_list
		tables_to_spool=[]
		for oid in items:
			#print(oid)
			tables_to_spool.append ((tl.GetItem(oid).GetText(), tl.GetItem(oid,1).GetText(), tl.GetItem(oid,2).GetText()))
		
		dropSource.SetData(data)

		#next line will make the drop target window come to top, allowing us
		#to get the info we need to do the work, if it's Explorer
		result = dropSource.DoDragDrop(0)

		#get foreground window hwnd
		h = win32gui.GetForegroundWindow()

		#get explorer location
		
		s = gencache.EnsureDispatch('Shell.Application')
		#s = win32com.client.Dispatch("Shell.Application")
		loc, outdir = None, None
		for w in s.Windows():
			if int(w.Hwnd) == h:
				loc = w.LocationURL
		if loc:
			outdir = loc.split('///')[1]
			#print (outdir)
			
			outdir = unquote(outdir)
		print (outdir)
		#got what we need, now download to outfol
		#if outdir and os.path.isdir(outdir):
		#	self.dloadItems(event, outdir)

		self.spool_tables(tables_to_spool, outdir)
		return
	def spool_tables(self,table_list, out_dir):
		print ('in spooler')
		if 1:
			self.threads.append(TableSpooler(self, table_list, out_dir, self.log))	
			for t in self.threads:
				t.Start()		

def save_status():
	global job_status_file
	p = pp.PrettyPrinter(indent=4)
	with open(job_status_file, "w") as text_file:
		cfg= deepcopy(config.cfg)
		text_file.write('cfg=%s\nstatus=%s' % (p.pformat(cfg),p.pformat(job_status)))
		log.info (job_status_file, extra=d)			
max_pool_size=multiprocessing.cpu_count() * 2
class TestFrame(wx.Frame):

	def __init__(self, parent, id, title, size, style = wx.DEFAULT_FRAME_STYLE ):

		wx.Frame.__init__(self, parent, id, title, size=size, style=style)

		self.CreateStatusBar(1)

		log=Log()

		self.win = TestVirtualList(self, log)

def main(argv=None):
	if argv is None:
		argv = sys.argv

	# Command line arguments of the script to be run are preserved by the
	# hotswap.py wrapper but hotswap.py and its options are removed that
	# sys.argv looks as if no wrapper was present.
	#print "argv:", `argv`

	#some applications might require image handlers
	#wx.InitAllImageHandlers()

	app = wx.App()
	f = TableHunter(None, -1, "ColumnSorterMixin used with a Virtual ListCtrl",wx.Size(500,300))
	f.Show()
	app.MainLoop()

if __name__ == '__main__':
	#main()
	
	#for signame in ('SIGINT', 'SIGTERM'):
	#	loop.add_signal_handler(getattr(signal, signame), functools.partial(ask_exit, signame))		
	freeze_support()	
	p = argparse.ArgumentParser()
	p.add_argument("--job_config", action='append', default='table_hunter.config.py',type=lambda kv: kv.split("="), dest='job_config')	
	p.add_argument("--pool_size", action='append',default=6,	 type=lambda kv: kv.split("="), dest='pool_size')	
	p.add_argument("--array_size", action='append',default=200000,	 type=lambda kv: kv.split("="), dest='array_size')	
	p.add_argument("--compress", action='append',default=0,	 type=lambda kv: kv.split("="), dest='compress')	
	p.add_argument("--column_delimiter", action='append',default='|',	 type=lambda kv: kv.split("="), dest='column_delimiter')	
	
	opt = p.parse_args() 
	optd = vars(opt)
	conf_path = os.getcwd()
	config_file = os.path.join(conf_path,'config', opt.job_config[0])
	if not os.path.isfile(config_file):
		config_file = os.path.join(conf_path, opt.job_config[0])
	assert os.path.isfile(config_file), 'Cannot find config file\n%s.' % config_file
	print (1,config_file)
	config=import_module(config_file)

	class MyApp(wx.App,wx.lib.mixins.inspection.InspectionMixin):
		
		app_version = __version__
		app_path = os.getcwd()
		app_name = os.path.basename(sys.argv[0].split('.')[0])
		help_file = app_name + '.htb'
		settings_name = os.path.join(app_path,'cfg', app_name + '.cfg')
		if not os.path.isfile(settings_name):
			settings_name = os.path.join(app_path, app_name + '.cfg')
		assert os.path.isfile(settings_name), 'Coannot find app settings file\n%s.' % settings_name
		print(2,settings_name)
		#app_config_loc=os.path.join(home,'config','app_config.py')
		
		def OnInit(self):
			global log, init
			#ac=import_module(app_config_loc)

			self.Init()
			if 1:
				self.settings = open_settings(self.settings_name)
				name_user = wx.GetUserId()
				name_instance = self.app_name + '::'
				self.instance_checker = wx.SingleInstanceChecker(name_instance + name_user)
				if self.instance_checker.IsAnotherRunning():
					wx.MessageBox(_('Software is already running.'), _('Warning'))
					return False
			self.frame = TableHunter(None, -1, 'Table Hunter',app = self, log=log, ts_out_dir=init.ts_out_dir, config=config) #main_frame(None, app = self,  title = 'Name/version')
			
			self.SetTopWindow(self.frame)
			self.frame.Show()
			return True 
	def start_gui(data):
		app = MyApp(redirect=False) #=True,filename="applogfile.txt")
		app.frame.Layout()
		try:
			app.MainLoop()
		except Exception as e:
			print('#'*80)
			traceback.print_exc();
			print('#'*80)
			raise
		
		
	try:
		_count = int(open("counter").read())
	except IOError:
		_count = 0


	if opt.pool_size> max_pool_size:	
		pool_size=max_pool_size
		log.warn('pool_size value is too high. Setting to %d (cpu_count() * 2)' % max_pool_size)
	else:
		pool_size=opt.pool_size	
	#parser = argparse.ArgumentParser(description=app_title)
	#parser.add_argument('-s','--session',default='',type=str,  help='Session file to open')
	#args = parser.parse_args()
	#default_session=None
	#if hasattr(args, 'session') and args.session:
	#	default_session=args.session
	start_gui(1)
	if 0:
		app = wx.App(False)
		TableHunter(None, -1, 'File Hunter')
		app.MainLoop()
	atexit.register(save_status)	
