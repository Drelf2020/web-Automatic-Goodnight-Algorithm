from logging import StreamHandler
from pywebio.output import put_markdown


GLOBAL_LOGLIST = None

class WebHandler(StreamHandler):

    def __init__(self, stream=None, loglist=None):
        super().__init__(stream)
        global GLOBAL_LOGLIST
        if not GLOBAL_LOGLIST:
            self.loglist = loglist
            GLOBAL_LOGLIST = loglist
        else:
            self.loglist = GLOBAL_LOGLIST

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            self.loglist.append(msg)
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)