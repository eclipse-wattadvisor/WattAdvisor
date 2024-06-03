"""Copyright (c) 2007, Eclipse Foundation, Inc. and its licensors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
"""

import logging


class LoggerWriter(object):
    def __init__(self, writer: logging.Logger):
        """Custom writer object for the `logging` module to redirect `sys.sdtout` and `sys.stderr` to a logger.

        Parameters
        ----------
        writer : logging.Logger
            Logger to redirect `sys.sdtout` and `sys.stderr` to
        """

        self._writer = writer
        self._msg = ''

    def write(self, message: str):
        """Appends new messages to logging channel.

        Parameters
        ----------
        message : str
            Message to append to logging channel
        """

        self._msg = self._msg + message
        while '\n' in self._msg:
            pos = self._msg.find('\n')
            self._writer(self._msg[:pos])
            self._msg = self._msg[pos+1:]

    def flush(self):
        """Flushes the logging channel
        """

        if self._msg != '':
            self._writer(self._msg)
            self._msg = ''