from logging import StreamHandler


GLOBAL_LOGLIST = None

class WebHandler(StreamHandler):

    def __init__(self, stream=None, loglist=None, dot=False):
        super().__init__(stream)
        self.dot = dot
        global GLOBAL_LOGLIST
        if not GLOBAL_LOGLIST:
            self.loglist = loglist
            GLOBAL_LOGLIST = loglist
        else:
            if loglist:
                self.loglist = loglist
            else:
                self.loglist = GLOBAL_LOGLIST

    def emit(self, record):
        try:
            msg = self.format(record)
            cid = msg.split('.')[-1]
            if self.dot:
                self.loglist.append((cid, msg.replace(f'.{cid}', '')))
            else:
                self.loglist.append(msg)
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)