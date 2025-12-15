@REM The Python launcher "py" must be accessible via the PATH environment variable.
@REM We assume that this batch script lies next to udapy in udapi-python/bin.
@REM The PYTHONPATH environment variable must contain path to udapi-python.
py %~dp$PATH:0\udapy %*
