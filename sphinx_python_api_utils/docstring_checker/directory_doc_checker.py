import os

from file_doc_checker import FileDocChecker

_EXCLUDES = ["make_rst.py","va_benchmark.py"]

def check_directory(path):
    for root, dirs, files in os.walk(os.path.realpath(path), topdown=True):
        for name in files:
            if name.endswith(".py"):
                if name in _EXCLUDES:
                    print "ignoring: " + name
                else:
                    fileDocChecker = FileDocChecker(os.path.join(root, name))
                    fileDocChecker.check_all_docs()

        # if "integration_tests" in dirs:
        #    dirs.remove("integration_tests")
        # if "intergration_tests" in dirs:
        #    dirs.remove("intergration_tests")
        # if "unittests" in dirs:
        #     dirs.remove("unittests")
        # if "uinit_test_objects" in dirs:
        #     dirs.remove("uinit_test_objects")
        # Not ready to check
        if root.endswith("PACMAN"):
            if "unittests" in dirs:
                dirs.remove("unittests")
            if "uinit_test_objects" in dirs:
                dirs.remove("uinit_test_objects")
        # Not ready to check
        if root.endswith("sPyNNaker"):
            if "unittests" in dirs:
                dirs.remove("unittests")
            if "integration_tests" in dirs:
                dirs.remove("integration_tests")
        # differenc docstring style
        if root.endswith("spalloc_server") and "docs" in dirs:
            dirs.remove("docs")


if __name__ == "__main__":
    check_directory("../../")
    """
    sPyNNakerExtraModelsPlugin
    sPyNNakerExternalDevicesPlugin
    """