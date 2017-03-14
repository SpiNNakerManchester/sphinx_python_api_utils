all_classes_dict = dict()

STATELESS_MODULES = ['', 'Enum', 'object', 'property', 'type']
THREAD_MODULES = ['Thread']
EXCEPTION_MODULES = ['Exception', 'KeyError', 'TypeError', 'ValueError']

# State Levels
MARKER = 0
STATELESS = MARKER + 1
NORMAL = STATELESS + 1
SLOTLESS = NORMAL + 1
THREAD = SLOTLESS + 1
EXCEPTION = THREAD + 1

STATE_NAMES = {MARKER: "Marker", STATELESS: "Stateless", NORMAL: "Normal",
               SLOTLESS: "Slotless", THREAD: "Thread", EXCEPTION: "Exception"}


class ClassInfo(object):

    __slots__ = ("_methods", "_name",
                 "_slots", "_state", "_subs", "_supers")

    @staticmethod
    def info_by_name(name):
        if name in all_classes_dict:
            return all_classes_dict[name]
        else:
            return ClassInfo(name)

    @staticmethod
    def all_classes():
        return all_classes_dict.values()

    def __init__(self, class_name):
        self._name = class_name
        self._slots = None
        self._methods = []
        self._subs = set()
        self._supers = set()
        self._state = None
        all_classes_dict[class_name] = self

    def add_method(self, method):
        self._methods.append(method)

    def add_sub_by_name(self, name):
        if name in EXCEPTION_MODULES:
            self._state = EXCEPTION
        elif name in THREAD_MODULES:
            self._state = THREAD
        elif name in STATELESS_MODULES:
            pass
        else:
            sub = self.info_by_name(name)
            sub._supers.add(self)
            self._subs.add(sub)

    def gv_name(self):
        if self._name in ["Graph"]:
            return "\"" + self._name + "\""
        return self._name

    def add_graph_lines(self, file, by_subs=True):
        if by_subs:
            for sub in self._subs:
                file.write("\t {} -> {}\n".format(
                    self.gv_name(), sub.gv_name()))
        else:
            for super in self._supers:
                file.write("\t {} -> {}\n".format(
                    super.gv_name(), self.gv_name()))

    @property
    def state(self):
        if self._state is None:
            if len(self._methods) == 0:
                self._state = MARKER
            else:
                self._state = STATELESS
            if self._slots is None:
                self._state = max(self._state, SLOTLESS)
            elif len(self._slots) > 0:
                self._state = max(self._state, NORMAL)
            for sub in self._subs:
                self._state = max(self._state, sub.state)
        return self._state

    @property
    def state_name(self):
        return STATE_NAMES[self.state]

    @property
    def name(self):
        return self._name

    @property
    def slots(self):
        return self._slots

    @slots.setter
    def slots(self, slots):
        self._slots = slots

    @property
    def methods(self):
        return self._methods

    @property
    def subs(self):
        return self._subs

    @property
    def supers(self):
        return self._supers

    def __str__(self):
        return self._name
