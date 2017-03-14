class FileInfo(object):

    __slots__ = ("_path", "_classes", "_errors")

    def __init__(self, path):
        self._path = path
        self._errors = []
        self._classes = []

    def add_error(self, error):
        self._errors.append(error)

    def add_class(self, class_info):
        self._classes.append(class_info)

    def print_errors(self):
        for error in self._errors:
            print error

    def print_classes(self):
        for class_info in self._classes:
            print class_info.name

    def add_graph_lines(self, file, by_subs=True):
        for class_info in self._classes:
            class_info.add_graph_lines(file, by_subs)

    def add_path_lines(self, file):
        for class_info in self._classes:
            file.write("{},{},{}\n".format(
                class_info.name, self.path, class_info.state_name))

    def has_error(self):
        return len(self._errors) > 0

    @property
    def path(self):
        return self._path

    @property
    def errors(self):
        return self._errors

    @property
    def classes(self):
        return self._classes
