# TableHunter-For-Oracle
Oracle Table data spooler for desktop.



## Prerequisits
You need:
   - Python 3.5 or later.
   - wxPython 3.0 (Phoenix)
   - Oracle client for this code to work because cx_Oracle uses OCI libs.



Set these in you CLI:
   - set ORACLE_HOME=C:\app\abuzunov-local\product\11.2.0\client_1 (64 bit client)
   - set PATH=%PATH%;%ORACLE_HOME%
   - init_job.bat table-hunter
   - set table-hunter0connectors0DEVdb='db password'
   - set NLS_LANG=...

## Database config
Set connect string in file table_hunter.config.py (line2)
```
...
{'connectors':{'DEVdb':'scott@localhost:1521/ORCL12'},
...
```

## Execute using Python
```
th.bat
C:\Python35-64>python table_hunter.py
```
## Execute in Windows CLI
   - Download latest 
   - Modify table_hunter.config.py (change DB connection string on line 2)
```
cd TableHunter
th.bat
table_hunter.exe
```


## Drag-n-Drop
Drag-n-Drop Oracle table from list to your desktop.
Wait for it to finish data spool.



