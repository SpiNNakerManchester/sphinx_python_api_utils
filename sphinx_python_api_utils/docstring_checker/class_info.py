all_classes = dict()

standard_modules = ['', 'Exception', 'Enum', 'install', 'KeyError', 'object', 'property',
                    'Thread', 'type', 'TypeError',
                    'ValueError']

class ClassInfo(object):

    __slots__ = ("_name","_slots","_methods", "_subs","_supers")

    @staticmethod
    def info_by_name(name):
        if name in all_classes:
            return all_classes[name]
        else:
            return ClassInfo(name)

    @staticmethod
    def all_classes():
        return all_classes.values()

    def __init__(self, class_name):
        self._name = class_name
        self._slots = None
        self._methods = []
        self._subs = set()
        self._supers = set()
        all_classes[class_name] = self

    def add_slots(self,slots):
        self._slots = slots

    def add_method(self, method):
        self._method.append(method)

    def add_sub_by_name(self, name):
        if not name in standard_modules:
            sub = self.info_by_name(name)
            sub._supers.add(self)
            self._subs.add(sub)

    def gv_name(self):
        if self._name in ["Graph"]:
            return "\"" + self._name + "\""
        return self._name

    def add_graph_lines(self, file, by_subs = True):
        if by_subs:
            for sub in self._subs:
                file.write("\t {} -> {}\n".format(self.gv_name(), sub.gv_name()))
        else:
            for super in self._supers:
                file.write("\t {} -> {}\n".format(super.gv_name(), self.gv_name()))

    @property
    def name(self):
        return self._name

    @property
    def slots(self):
        return self._slots

    @property
    def methods(self):
        return self._method

    @property
    def subs(self):
        return self._subs

    @property
    def supers(self):
        return self._supers

    def __str__(self):
        return self._name

