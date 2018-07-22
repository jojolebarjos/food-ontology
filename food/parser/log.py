# -*- coding: utf-8 -*-


import asyncio
from datetime import datetime
import io


# Basic log manager
class Log:
    def __init__(self, path, executor):
        self._executor = executor
        self._file = io.open(path, 'a', encoding='utf-8', newline='\n')
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
