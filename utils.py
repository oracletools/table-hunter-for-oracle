from __future__ import print_function
import os,imp
import pprint as pp
import socket 
import sys
import datetime as dt
import errno
import traceback
from socket import error as socket_error
e=sys.exit
#builtins: init, config 
def formatExceptionInfo(maxTBlevel=5):
	cla, exc, trbk = sys.exc_info()
	excName = cla.__name__
	try:
		excArgs = exc.__dict__["args"]
	except KeyError:
		excArgs = "<no args>"
	excTb = traceback.format_tb(trbk, maxTBlevel)
	return (excName, excArgs, excTb)
def create_symlink(from_dir, to_dir, home):
	global log
	os.chdir(home)
	#print(home)
	if (os.name == "posix"):
		#os.unlink(to_dir)
		#if not os.path.isdir(to_dir):
		os.symlink(from_dir, to_dir)
		#print (from_dir)
		#print (to_dir)
		#e(0)
	elif (os.name == "nt"):
		from subprocess import Popen, PIPE, STDOUT

		wget = Popen(('mklink /J %s %s' % (to_dir, from_dir)).split(' '), stdout=PIPE, stderr=STDOUT, shell=True)
		stdout, nothing = wget.communicate()    
		log.info(stdout, extra=d)
		#print stdout
		#os.system('mklink /J %s %s' % (to_dir, from_dir))
	else:
		log.error('Cannot create symlink. Unknown OS.', extra=d)
def unlink(dirname):
	if (os.name == "posix"):
		os.unlink(dirname)
	elif (os.name == "nt"):
		#print('deleting', os.getpid(), dirname)
		try:
			os.rmdir( dirname )
		except:
			pass
	else:
		log.error('Cannot unlink. Unknown OS.', extra=d)
def import_module(filepath):
	class_inst = None
	mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
	assert os.path.isfile(filepath), 'File %s does not exists.' % filepath
	if file_ext.lower() == '.py':
		py_mod = imp.load_source(mod_name.replace('.','_'), filepath)

	elif file_ext.lower() == '.pyc':
		py_mod = imp.load_compiled(mod_name, filepath)
	return py_mod

