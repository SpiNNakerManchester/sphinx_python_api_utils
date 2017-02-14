class DocException(Exception):

    def __init__(self, path, error, line_num):
        self._path = path
        self._error = error
        self._line_number = line_num
        print self

    def __str__(self):
        return repr(self._error + " in: " + self._path + ":" +
                    str(self._line_number))
