"""
Usage:
	from  lib.init_job import init
	TIMESTAMP, JOB_NAME, TRADE_DATE, HOME = init()
"""
import os, sys
import logging
from pprint import pprint
from copy import deepcopy
import time

assert 'BACKUP_JOB_NAME' in os.environ.keys(), 'Backup job name is not defined.'
assert 'BACKUP_TIMESTAMP' in os.environ.keys(), 'Backup timestamp is not set.'
os.environ['BACKUP_IMP_DATE']=os.environ['BACKUP_TIMESTAMP']
assert 'BACKUP_IMP_DATE' in os.environ.keys(), 'Backup imp date is not set.'
e=sys.exit
os.environ['BACKUP_IMP_DATE']=os.environ['BACKUP_TIMESTAMP']
ts, JOB_NAME, TRADE_DATE, HOME = os.environ['BACKUP_TIMESTAMP'], os.environ['BACKUP_JOB_NAME'], os.environ['BACKUP_IMP_DATE'], os.environ['BACKUP_HOME']

latest_dir =os.path.join(HOME,'log',JOB_NAME,'latest')
ts_dir=os.path.join(HOME,'log',JOB_NAME,ts)
if not os.path.exists(ts_dir):
	os.makedirs(ts_dir)

def init():
	return ts, JOB_NAME, TRADE_DATE, HOME, log, ts_dir

DEBUG=1
d = {'pid':pid,'method':'main','script':script_name, 'rows':0}	
FORMAT = '%(levelname)s|%(asctime)s|%(pid)d|%(name)s|%(script)s|%(method)s|%(message)s'


lfile=os.path.join(ts_dir,'%s_%d.log' % (script_name,pid))
#deleting existing log file
if os.path.isfile(lfile):
	os.unlink(lfile)
logging.basicConfig(filename=lfile,level=logging.INFO,format=FORMAT)
log = logging.getLogger(JOB_NAME)
log.setLevel(logging.DEBUG)

log = logging.getLogger(JOB_NAME)
#log.warn('test', extra=d)

import builtins
script_name=os.path.splitext(__file__)[0]
builtins.log=log
builtins.script_name=script_name
builtins.d=d
from utils import create_symlink, unlink, import_module


config_home = os.path.join(HOME,'config')

ts_out_dir=os.path.join(HOME,'log',JOB_NAME,ts,'output')
latest_out_dir =os.path.join(HOME,'log',JOB_NAME,'latest','output')
ts_cfg_dir=os.path.join(HOME,'log',JOB_NAME,ts,'config')
latest_cfg_dir =os.path.join(HOME,'log',JOB_NAME,'latest','config')
done_file= os.path.join(ts_dir,'DONE.txt')
ts_status_dir= os.path.join(ts_dir, 'status')
job_status_file=os.path.join(ts_status_dir,'%s.%s.status.py' % (script_name,JOB_NAME))	

if not os.path.exists(ts_status_dir):
	os.makedirs(ts_status_dir)
if not os.path.exists(ts_cfg_dir):
	os.makedirs(ts_cfg_dir)
	
if not os.path.exists(ts_out_dir):
	os.makedirs(ts_out_dir)	
if  os.path.exists(latest_dir):	
	unlink(latest_dir)
	
create_symlink(ts_dir, latest_dir, HOME)
#if  os.path.exists(latest_out_dir):
#	rmdir(latest_out_dir)
#os.symlink(ts_out_dir, latest_out_dir)
#print (latest_out_dir)
#create_symlink(ts_out_dir, latest_out_dir, HOME)
	

hide_log_output = False
if not hide_log_output:
	ch = logging.StreamHandler(sys.stdout)
	ch.setLevel(logging.DEBUG)
	formatter = logging.Formatter(FORMAT)
	ch.setFormatter(formatter)
	log.addHandler(ch)
log.info('Log file:\n%s' % lfile, extra=d)

def timing(f):
	def wrap(*args, **kargs):
		global d
		d = deepcopy(d)
		d['pid'] =os.getpid()
		time1 = time.time()
		ret = f(*args, **kargs)
		time2 = time.time()
		d['method'] =f.func_name
		log.info ('Elaplsed: %0.3f ms' % ( (time2-time1)*1000.0), extra=d)
		return ret
	return wrap	
	
