from enum import Enum

from doc_exception import DocException

CodeState = Enum(
    value="CODE_STATE",
    names=[
        ("START", "start"),
        ("CODE", "code"),
        ("IN_CLASS", "in class"),
        ("AFTER_CLASS", "after class"),
        ("CLASS_DOC", "class doc"),
        ("IN_DEF", "def"),
        ("AFTER_DEF", "after def"),
        ("DOCS_START", "doc start"),
        ("DOCS_START_AFTER_BLANK", "after blank"),
        ("DOCS_DECLARATION", "declarion"),
        # ("DOCS_END", "end"),
        # ("IN_PARAM", "param"),
        ]
)

_CRITICAL = 1
_WRONG = _CRITICAL + 1
_HIDDEN = _WRONG + 1
_UNEXPECTED = _HIDDEN + 1
_MISSING = _UNEXPECTED + 1
_NO_DOCS = _MISSING + 1

OK = None


class FileDocChecker:
    """" test for class start

    :param python_path: path to file to check
    can be more than one line long
    """

    _python_path = None
    _code_state = CodeState.START
    _part_line = ""
    _lineNum = 0
    _param_indent = None
    _previous_indent = None

    def __init__(self, python_path, debug=False):
        print python_path
        self._python_path = python_path
        self._debug = debug

    def check_all_docs(self):
        with open(self._python_path, "r") as python_file:
            for line in python_file:
                self._check_line(line.rstrip().split("#")[0].rstrip())

    def _check_line(self, line):
        if self._debug:
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
        # elif self._code_state == CodeState.DOCS_END:
        #    self._check_in_doc_end(line)
        # elif self._code_state == CodeState.IN_PARAM:
        #    self._check_in_param(line)
        else:
            print self._code_state
            raise NotImplementedError
        if self._debug:
            print str(self._lineNum) + "   " + str(self._code_state)

    def _check_in_start(self, line):
        stripped = line.strip()
        if "\"\"\"" in stripped:
            self._code_state = CodeState.CLASS_DOC
            return OK
        return self._code_check(stripped)

    def _code_check(self, stripped):
        if stripped.startswith("class"):
            return self._check_in_class(stripped)
        if stripped.startswith("def "):
            return self._check_in_def(stripped)
        return OK

    def _check_in_code(self, line):
        stripped = line.strip()
        if "\"\"\"" in stripped:
            return self._report(line, "unexpected doc", _HIDDEN)
        return self._code_check(stripped)

    def _check_in_class(self, line):
        if line.endswith(":"):
            self._code_state = CodeState.AFTER_CLASS
            return OK
        else:
            self._code_state = CodeState.IN_CLASS
            if "\"\"\"" in line:
                msg = "unexpected doc start in class declaration"
                return self._report(line, msg, _CRITICAL)
            else:
                return OK

    def _check_after_class(self, line):
        stripped = line.strip()
        if stripped.startswith("\"\"\""):
            parts = stripped.split("\"\"\"")
            if len(parts) <= 2:
                self._code_state = CodeState.CLASS_DOC
                return OK
            elif len(parts) == 3:
                if len(parts[2]) == 0:
                    self._code_state = CodeState.CODE
                else:
                    msg = "unexpected stuff after one line doc end"
                    return self._report(line, msg, _UNEXPECTED)
            else:
                msg = "three doc tags found in one line"
                return self._report(line, msg, _UNEXPECTED)
        elif len(stripped) == 0:
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

    def _check_in_def(self, line):
        self._code_state = CodeState.IN_DEF
        if line.endswith(":"):
            self._code_state = CodeState.AFTER_DEF
            return OK
        if "\"\"\"" in line:
            msg = "unexpected doc start in def declaration"
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
        self._code_state = CodeState.CODE
        return OK

    def _check_in_doc_start(self, line):
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
        return self._report(line, msg, _UNEXPECTED)

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
            if not stripped.startswith(":py"):
                msg = "Unxpected : line in param doc section"
                return self._report(line, msg, _CRITICAL)
        if indent <= self._param_indent:
            print self._param_indent
            print indent
            msg = "Unxpected non indented line in param doc section"
            return self._report(line, msg, _CRITICAL)
        # if self._previous_indent == None:
        #    self._previous_indent = indent
        #     return OK
        # if self._previous_indent == indent:
        #     return OK
        # msg = "Unxpected indent line in param doc section. Only 1 level allowed"
        # return self._report(line, msg, _CRITICAL)
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
                    return OK
            return self._report(line, "paramater name must end with :",
                                _CRITICAL)
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
            return self._report(line, "singleton :return possible :rtype: None",
                                _UNEXPECTED)
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
                print parts
                if len(parts[2]) > 0 and parts[2][-1] == ":":
                    return OK
            return self._report(line, "paramater name must end with :",
                                _MISSING)
        return OK


#    def _check_in_param(self, line):
#        stripped = line.strip()
#        if len(stripped) == 0:
#            # self._code_state = CodeState.DOCS_END
#            return OK
#        if stripped[0] == ":":
#            self._code_state = CodeState.DOCS_DECLARATION
#            return self._check_in_doc_declaration(line)
#        if stripped[0] == "*":
#            return OK
#        if stripped.startswith("http"):
#            return OK
#        if stripped.startswith("\"\"\""):
#            return self._end_docs(line)
        # return self._report(line, "unexpected :param second line",
        #                    _CRITICAL)

    # def _check_in_doc_end(self, line):
    #    stripped = line.strip()
    #    if stripped.startswith("\"\"\""):
    #        return self._end_docs(line)
    #    if stripped.startswith(":param"):
    #        return self._report(line, ":param after blank line",
    #                            _HIDDEN)
    #    if stripped.startswith(":return"):
    #        return self._report(line, ":return after blank line",
    #                            _HIDDEN)

    def _report(self, line, msg, level):
        print self._python_path + ":" + str(self._lineNum)
        print line
        print msg
        if level < _MISSING or self._debug:
            raise DocException(self._python_path, msg, self._lineNum)

if __name__ == "__main__":
    import os
    path = os.path.realpath(__file__)

    file_doc_checker = FileDocChecker(path, True);
    file_doc_checker.check_all_docs();
