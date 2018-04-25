set BACKUP_JOB_NAME=%1

for /f "tokens=1-4 delims=/ " %%i in ("%date%") do (
     set dow=%%i
     set month=%%j
     set day=%%k
     set year=%%l
)
set datestr=%month%_%day%_%year%
echo datestr is %datestr%
set BACKUP_TIMESTAMP=%datestr%
set BACKUP_HOME=%cd%
