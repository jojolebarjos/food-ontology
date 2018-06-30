# -*- coding: utf-8 -*-


import asyncio
from datetime import datetime
import io
import os


# Get local directory
HERE = os.path.dirname(os.path.realpath(__file__))
SERVER_LOG = os.path.join(HERE, 'server.log')


# Basic log manager
class Log:
    def __init__(self, executor):
        self._executor = executor
        self._path = SERVER_LOG
        self._file = io.open(self._path, 'a', encoding='utf-8', newline='\n')
        self._lock = asyncio.Lock()
        self._print('Log file open')
    
    # Print to console and file
    def _print(self, text):
        now = datetime.now()
        line = '%s: %s' % (now.isoformat(' '), text)
        print(text)
        self._file.write('%s\n' % line)
        self._file.flush()
    
    # Write text to log
    async def info(self, text):
        loop = asyncio.get_event_loop()
        async with self._lock:
            return await loop.run_in_executor(self._executor, self._print, text)
