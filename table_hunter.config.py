cfg=\
{'connectors':{'DEVdb':'scott@localhost:1521/ORCL12'}, 
 'nls_param_sets': {'set1':"""
NLS_DATE_FORMAT	= 'DD-MON-RR HH24:MI:SS'
NLS_TIMESTAMP_FORMAT	='DD-MON-RR HH24:MI:SS.FF3'
NLS_TIMESTAMP_TZ_FORMAT	='DD-MON-RR HH:MI:SS.FF3 TZH:TZM'
"""},
 'profile': {'default': {'from': 'DEVdb','nls_params': 'set1',},

			   }}


