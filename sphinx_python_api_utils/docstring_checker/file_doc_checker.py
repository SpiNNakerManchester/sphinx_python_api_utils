from enum import Enum
import re
from doc_exception import DocException
from file_info import FileInfo
from class_info import ClassInfo

# States the file can be in when reading the next line
CodeState = Enum(
    value="CODE_STATE",
    names=[
        ("START", "start"),
        ("CODE", "code"),
        ("IN_CLASS", "in class"),
        ("AFTER_CLASS", "after class"),
        ("CLASS_DOC", "class doc"),
        ("IN_SLOTS", "in slots"),
        ("IN_DEF", "def"),
        ("AFTER_DEF", "after def"),
        ("DOCS_START", "doc start"),
        ("DOCS_START_AFTER_BLANK", "after blank"),
        ("DOCS_DECLARATION", "declarion"),
        ("COMMENT", "comment"),
        # ("DOCS_END", "end"),
        # ("IN_PARAM", "param"),
        ]
)

# Error levels
_CRITICAL = 1
_WRONG = _CRITICAL + 1
_HIDDEN = _WRONG + 1
_UNEXPECTED = _HIDDEN + 1
_MISSING = _UNEXPECTED + 1
_NO_DOCS = _MISSING + 1
_STYLE = _NO_DOCS + 1

# Return if no erro found
OK = None

INIT = "init"
PRIVATE = "private"
PUBLIC = "public"


def rreplace(s, old, new, occurrence=-1):
    """
    Helper function to do right replace

    :param s: String to replace into
    :param old: Values being replaced
    :param new: new Values being inserted
    :param occurrence: Number of times a replacement should be done
        Default -1 is to replace all found
    :return: new String with replacements
    """
    li = s.rsplit(old, occurrence)
    return new.join(li)


class FileDocChecker(object):
    """"
    Sets the Class up to test a file assumes to be python
    with sphiunx style docstrings

    """

    _code_state = CodeState.START
    _part_line = ""
    _lineNum = 0
    _param_indent = None
    _def_string = ""
    _def_type = None
    _def_params = []
    _doc_params = []
    _doc_types = []
    _def_name = None
    info = None
    cl_info = None
    test_class = None

    def __init__(self, python_path, root = "", kill_on_error=False, debug=False):
        """"

        :param python_path: path to file to check
            can be more than one line long
        """
        self.python_path = python_path
        self.test_class = ((python_path.find("/tests/") > 0) or
                           (python_path.find("/unittests/") > 0) or
                           (python_path.find("\\unittests\\") > 0) or
                           (python_path.find("/integration_tests/") > 0) or
                           (python_path.find("\\integration_tests\\") > 0))
        self.debug = debug
        self.kill_on_error = kill_on_error
        self.info = FileInfo(python_path[len(root):])

    def check_all_docs(self):
        if self.debug:
            print self.python_path
        with open(self.python_path, "r") as python_file:
            for line in python_file:
                self._check_line(line.rstrip().split("#")[0].rstrip())
        return self.info

    def _check_line(self, line):
        if self.debug:
            print line
        self._lineNum += 1
        if line.strip().endswith("\\"):
            self._part_line = self._part_line + line[:-1] + " "
            return
        else:
            if len(self._part_line) > 0:
                line = self._part_line + line
                self._part_line = ""

        if self._code_state == CodeState.START:
            self._check_in_start(line)
        elif self._code_state == CodeState.CODE:
            self._check_in_code(line)
        elif self._code_state == CodeState.IN_CLASS:
            self._check_in_class(line)
        elif self._code_state == CodeState.AFTER_CLASS:
            self._check_after_class(line)
        elif self._code_state == CodeState.CLASS_DOC:
            self._check_in_class_doc(line)
        elif self._code_state == CodeState.IN_SLOTS:
            self._check_in_slots(line)
        elif self._code_state == CodeState.IN_DEF:
            self._check_in_def(line)
        elif self._code_state == CodeState.AFTER_DEF:
            self._check_after_def(line)
        elif self._code_state == CodeState.DOCS_START:
            self._check_in_doc_start(line)
        elif self._code_state == CodeState.DOCS_START_AFTER_BLANK:
            self._check_in_doc_start_after_blank(line)
        elif self._code_state == CodeState.DOCS_DECLARATION:
            self._check_in_doc_declaration(line)
        elif self._code_state == CodeState.COMMENT:
            self._check_in_comment(line)
        # elif self._code_state == CodeState.DOCS_END:
        #    self._check_in_doc_end(line)
        # elif self._code_state == CodeState.IN_PARAM:
        #    self._check_in_param(line)
        else:
            print self._code_state
            raise NotImplementedError
        if self.debug:
            print str(self._lineNum) + "   " + str(self._code_state)

    def _check_in_start(self, line):
        if "\"\"\"" in line:
            return self._verify_doc_start(line, CodeState.CLASS_DOC,
                                          CodeState.START)
        stripped = line.strip()
        return self._code_check(stripped)

    def _verify_doc_start(self, line, doc_state, none_doc_state):
        stripped = line.strip()
        if stripped.startswith("r\"\"\""):
            stripped = stripped[1:]
        elif not stripped.startswith("\"\"\""):
            msg = "unexpected doc tags"
            return self._report(line, msg, _UNEXPECTED)
        parts = stripped.split("\"\"\"")
        if len(parts) <= 2:
            self._code_state = doc_state
            return OK
        elif len(parts) == 3:
            if len(parts[2]) == 0:
                self._code_state = none_doc_state
                return OK
            else:
                msg = "unexpected stuff after one line doc end"
                return self._report(line, msg, _UNEXPECTED)
        else:
            msg = "three doc tags found in one line"
            return self._report(line, msg, _UNEXPECTED)

    def _code_check(self, stripped):
        if stripped.startswith("class "):
            return self._check_in_class(stripped)
        if stripped.startswith("def "):
            return self._check_in_def(stripped)
        if stripped.startswith("__slots__"):
            return self._check_in_slots(stripped)
        return OK

    def _check_in_code(self, line):
        if "\"\"\"" in line:
            return self._verify_doc_start(line, CodeState.COMMENT,
                                          CodeState.CODE)
        stripped = line.strip()
        return self._code_check(stripped)


    def _check_in_class(self, line):
        self._def_string += line
        if line.endswith(":"):
            self._extract_class_def(line)
            self._code_state = CodeState.AFTER_CLASS
            return OK
        else:
            self._code_state = CodeState.IN_CLASS
            if "\"\"\"" in line:
                msg = "unexpected doc start in class declaration"
                return self._report(line, msg, _CRITICAL)
            else:
                return OK

    def _extract_class_def(self, line):
        if not self.test_class:
            declaration = self._def_string.replace(" ","")
            cl_name = declaration[5:declaration.index("(")]
            if cl_name == "(":
                print self.python_path + ":" + str(self._lineNum)
            self.cl_info = ClassInfo.info_by_name(cl_name)
            if not cl_name.startswith("_"):
                self.info.add_class(self.cl_info)
                subs_string = declaration[declaration.index("(")+1:declaration.index(")")]
                if subs_string.startswith("namedtuple"):
                    pass
                elif subs_string.startswith("collections."):
                    pass
                else:
                    subs = subs_string.split(",")
                    for sub in subs:
                        self._extract_subs(line, sub)
        self._def_string = ""

    def _extract_subs(self, line, sub):
        if sub.startswith("exceptions."):
            sub = sub[11:]
        if sub.startswith("_"):
            print self.python_path + ":" + str(self._lineNum)
        if sub.startswith("logging."):
            return
        else:
            self.cl_info.add_sub_by_name(sub)

    def _check_after_class(self, line):
        if "\"\"\"" in line:
            return self._verify_doc_start(line, CodeState.CLASS_DOC,
                                          CodeState.CODE)
        stripped = line.strip()
        if len(stripped) == 0:
            return OK
        else:
            self._code_state = CodeState.CODE
            return self._check_in_code(line)

    def _check_in_class_doc(self, line):
        stripped = line.strip()
        if stripped.startswith("\"\"\""):
            return self._end_docs(line)
        if stripped.startswith(":return"):
            msg = ":return does not make sense in class doc"
            return self._report(line, msg, _UNEXPECTED)
        return OK

    def _check_in_slots(self, line):
        self._code_state = CodeState.IN_SLOTS
        stripped = line.strip()
        if stripped.startswith("#"):
            return OK
        self._def_string += stripped
        if stripped.endswith(")"):
            declaration = self._def_string[self._def_string.index("(")+1:-1]
        elif stripped.endswith("]"):
            declaration = self._def_string[self._def_string.index("[")+1:-1]
        else:
            return OK
        declaration = declaration.replace(" ", "")
        declaration = declaration.replace("\"", "")
        declaration = declaration.replace("'", "")
        slots = declaration.split(",")
        self._def_string = ""
        self._code_state = CodeState.CODE
        return OK

    def _check_in_def(self, line):
        self._code_state = CodeState.IN_DEF
        self._def_string += line
        if line.endswith(":"):
            self._code_state = CodeState.AFTER_DEF
            return self._extract_params(line)
        if "\"\"\"" in line:
            msg = "unexpected doc start in def declaration"
            return self._report(line, msg, _UNEXPECTED)
        return OK

    def _extract_params(self, line):
        declaration = self._def_string.replace("(", " ", 1)
        declaration = rreplace(declaration, ")", " ",1)
        declaration = declaration.replace(",", " ")
        declaration = declaration.replace('"="', "x")
        declaration = re.sub("\(.*?\)", "junk", declaration)
        declaration = re.sub(' +', ' ', declaration)
        self._def_string = ""
        parts = declaration.split(" ")
        if (parts[0] != "def"):
            msg = "unexpected start in def declaration"
            return self._report(line, msg, _UNEXPECTED)
        self._def_name = parts[1]
        self._doc_params = []
        self._doc_types = []
        if (parts[1] == "__init__"):
            self._def_type = INIT
        elif (parts[1][0] == "_"):
            self._def_type = PRIVATE
        else:
            self._def_type = PUBLIC
        self._def_params = []
        if (parts[2] == "self"):
            start = 3
        else:
            start = 2
        for part in parts[start:-1]:
            if (part[0] == "=") or (part[-1] == "="):
                msg = "E251 unexpected spaces around keyword/parameter equals"
                return self._report(line, msg, _UNEXPECTED)
            param_parts = part.split("=")
            if len(param_parts) > 2:
                msg = "Multiple = found in one paramter"
                return self._report(line, msg, _UNEXPECTED)
            name = param_parts[0]
            if name[0] == "*":
                if len(name) == 1:
                    msg = "* only parameter name"
                    return self._report(line, msg, _UNEXPECTED)
                if name[1] == "*":
                    name = name[2:]
                else:
                    name = name[1:]
            self._def_params.append(name)
        if (parts[-1] != ":"):
            msg = "No : found at end of def declaration"
            return self._report(line, msg, _UNEXPECTED)
        return OK

    def _check_after_def(self, line):
        if "\"\"\"" in line:
            self._code_state = CodeState.DOCS_START
            parts = line.split("\"\"\"")
            if len(parts) == 1:
                # Ok just the doc start
                pass
            elif len(parts) == 2:
                return self._check_in_doc_start(parts[1])
            elif len(parts) == 3:
                # Ok start and end comment on same line
                self._code_state = CodeState.CODE
                pass
            else:
                print line
                print parts
                raise NotImplementedError
        # Oops no docs
        self._code_state = CodeState.CODE
        if self._def_type != PRIVATE:
            msg = "No Docs found for function " + self._def_name
            return self._report(line, msg, _NO_DOCS)
        return OK

    def _check_in_doc_start(self,
                            line):
        stripped = line.strip()
        if "\"\"\"" in stripped:
            return self._end_docs(line)
        if len(stripped) == 0:
            self._code_state = CodeState.DOCS_START_AFTER_BLANK
        if stripped.startswith(":py:"):
            return OK
        if stripped.startswith(":"):
            return self._report(line, ":param without blank line",
                                _HIDDEN)
        return OK

    def _end_docs(self, line):
        self._code_state = CodeState.CODE
        stripped = line.strip()
        if stripped == ("\"\"\""):
            return OK
        msg = "Closing quotes should be on their own line (See per-0257)"
        return self._report(line, msg, _STYLE)

    def _check_in_doc_start_after_blank(self, line):
        stripped = line.strip()
        if stripped.startswith("\"\"\""):
            return self._end_docs(line)
        if stripped.startswith(":py"):
            return OK
        if stripped.startswith(":"):
            self._code_state = CodeState.DOCS_DECLARATION
            return self._check_in_doc_declaration(line)
        if len(stripped) > 0:
            self._code_state = CodeState.DOCS_START
        return OK

    def _check_in_doc_declaration(self, line):
        stripped = line.strip()
        if len(stripped) == 0:
            return OK
        if stripped.startswith("\"\"\""):
            self._previous_indent = None
            return self._end_docs(line)
        # Line has already had a rstrip
        indent = len(line) - len(stripped)
        if stripped.startswith(":param"):
            self._param_indent = indent
            self._previous_indent = None
            return self._verify_param(line)
        if stripped.startswith(":type"):
            self._param_indent = indent
            self._previous_indent = None
            return self._verify_type(line)
        if stripped.startswith(":return"):
            self._param_indent = indent
            self._previous_indent = None
            return self._verify_return(line)
        if stripped.startswith(":rtype:"):
            self._param_indent = indent
            self._previous_indent = None
            return self._verify_rtype(line)
        if stripped.startswith(":raise"):
            self._param_indent = indent
            self._previous_indent = None
            return self._verify_raise(line)
        if stripped.startswith(":"):
            if stripped.startswith(":py"):
                return OK
            if stripped == "::":
                return OK
            msg = "Unxpected : line in param doc section"
            return self._report(line, msg, _CRITICAL)
        if indent <= self._param_indent:
            msg = "Unxpected non indented line in param doc section"
            return self._report(line, msg, _CRITICAL)
        return OK

    def _verify_param(self, line):
        stripped = line.strip()
        parts = stripped.split(' ')
        if parts[0] != ":param":
            return self._report(line, "No space after :param",
                                _CRITICAL)
        if len(parts) == 1:
            return self._report(line, "singleton :param",
                                _UNEXPECTED)
        if parts[1][-1] != ":":
            if len(parts) > 2:
                if parts[2][-1] == ":":
                    check = self._verify_param_name(parts[2], line)
                    if check == OK:
                        self._doc_types.append(parts[2][:-1])
                        if len(parts) == 3:  #: param type name:
                            msg = "parameter " + parts[2] + " in " + \
                                  self._def_name + " has no text"
                            return self._report(line, msg, _MISSING)
                    return check
            return self._report(line, "paramater name must end with :",
                                _CRITICAL)
        else:
            return self._verify_param_name(parts[1], line)
        return OK

    def _verify_param_name(self, name, line):
        name = name[:-1]
        if not name in self._def_params:
            msg = "param " + name + " not in parameter list " + \
                  str(self._def_params)
            return self._report(line, msg, _CRITICAL)
        self._doc_params.append(name)
        return OK

    def _verify_type(self, line):
        stripped = line.strip()
        parts = stripped.split(' ')
        if parts[0] != ":type":
            return self._report(line, "No space after :type",
                                _CRITICAL)
        if len(parts) == 1:
            return self._report(line, ":type requires a param_name: type",
                                _UNEXPECTED)
        if parts[1][-1] != ":":
            return self._report(line, "in type paramater_name must end with :",
                                _CRITICAL)
        else:
            report = self._verify_param_name(parts[1], line)
            if report != OK:
                return report
        if len(parts) == 2:
            # return self._report(line, ":type requires a param_name: type",
            #                   _MISSING)
            pass
        else:
            if parts[2].lower() == "bytestring":
                msg = "bytestring not a python type use str"
                return self._report(line, msg, _CRITICAL)

        return OK

    def _verify_rtype(self, line):
        stripped = line.strip()
        parts = stripped.split(' ')
        if parts[0] != ":rtype:":
            return self._report(line, "No space after :rtype:",
                                _CRITICAL)
        if len(parts) == 1:
            return self._report(line, ":rtype: requires a type",
                                _UNEXPECTED)
        return OK

    def _verify_raise(self, line):
        stripped = line.strip()
        parts = stripped.split(' ')
        if not parts[0] in [":raise", ":raise:", ":raises", ":raises:"]:
            return self._report(line, "No space after :raise",
                                _CRITICAL)
        if len(parts) == 1:
            return self._report(line, ":raise requires a type",
                                _UNEXPECTED)
        # if parts[1].lower().startswith("none"):
        #    return self._report(line, "Do not use :raise None", _UNEXPECTED)
        return OK

    def _verify_return(self, line):
        stripped = line.strip()
        parts = stripped.split(' ')
        if len(parts) == 1:
            msg = "singleton :return possible :rtype: None"
            return self._report(line, msg, _UNEXPECTED)
        if parts[0] != ":return":
            if parts[0] == ":return:":
                if parts[1].lower() == "none":
                    if len(parts) == 2:
                        msg = "replace :return: None with :rtype: None"
                        return self._report(line, msg, _UNEXPECTED)
                return OK
            else:
                return self._report(line, "No space after :return",
                                    _CRITICAL)
        if parts[1][-1] != ":":
            if len(parts) > 2:
                print "_verify_return"
                print parts
                if len(parts[2]) > 0 and parts[2][-1] == ":":
                    return OK
            return self._report(line, "paramater name must end with :",
                                _MISSING)
        return OK

    def _check_in_comment(self, line):
        stripped = line.strip()
        if "\"\"\"" in stripped:
            return self._end_docs(line)
        return OK

    def _report(self, line, msg, level):
        error = self.python_path + ":" + str(self._lineNum) + "  " + msg
        if not self.test_class:
            # print error
            pass
        if level < _MISSING:
            if self.kill_on_error:
                raise DocException(self.python_path, msg, self._lineNum)
            else:
                self.info.add_error(error)
        return error

if __name__ == "__main__":
    import os
    path = os.path.realpath(__file__)

    # path = "/brenninc/spinnaker/SpiNNMachine/spinn_machine/processor.py"
    path = "C:/Dropbox/spinnaker/PACMAN/pacman/model/graphs/application/impl/application_vertex.py"
    # file_doc_checker = FileDocChecker(path, True);
    file_doc_checker = FileDocChecker(path, False)
    info = file_doc_checker.check_all_docs()
    print "Errors"
    info.print_errors()
    print info.path
    info.print_classes()
    with open("graph.gv","w") as file:
        file.write("digraph G {\n")
        info.add_graph_lines(file)
        file.write("}")
