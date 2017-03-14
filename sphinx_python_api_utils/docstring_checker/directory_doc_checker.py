import os
import sys
from subprocess import call

from file_doc_checker import FileDocChecker
from class_info import ClassInfo

_EXCLUDES = ["va_benchmark.py"]
_HEAVIES =  ["AbstractHasLabel", "AbstractHasConstraints", "AbstractPopulationSettable","AbstractGeneratesDataSpecification"]

def find_groups_up_and_down(info, found):
    if info in found:
        return
    found.add(info)
    for sub in info.subs:
        find_groups_up_and_down(sub, found)
    if not info.name in _HEAVIES :
        for super in info.supers:
            find_groups_up_and_down(super, found)

def find_groups_up(info, found):
    if info in found:
        return
    found.add(info)
    for super in info.supers:
        find_groups_up(super, found)

def graph(infos, name, by_subs=True):
    gv_name = name + ".gv"
    png_name = name + ".png"
    with open(gv_name, "w") as file:
        file.write("digraph G {\n")
        for info in infos:
            info.add_graph_lines(file, by_subs)
        file.write("}")
    call(["dot", "-Tpng", gv_name, "-o", png_name])

def graph_infos_by_group(infos):
    graph_count = 0
    while len(infos) > 0:
        info = infos[0]
        if ((len(info.subs)) == 0 and (len(info.supers) ==0)) or (info.name in _HEAVIES):
            infos.remove(info)
        else:
            info_group = set()
            find_groups_up_and_down(info, info_group)
            graph_count += 1
            graph(info_group, "subs/graph{}".format(graph_count))
            for gr_info in info_group:
                if gr_info in infos:
                    infos.remove(gr_info)

def graph_by_sub(info):
    info_group = set()
    find_groups_up(info, info_group)
    graph(info_group, "subs/" + info.name, by_subs=False)

def graph_by_subs(infos):
    sub_infos = set()
    for info in infos:
        for sub in info.subs:
            if len(sub.subs) == 0:
                sub_infos.add(sub)
    for sub in sub_infos:
        graph_by_sub(sub)

def check_directory(path):
    infos = []
    error = False
    realpath = os.path.realpath(path)
    if os.path.isfile(realpath):
        fileDocChecker = FileDocChecker(realpath)
        info = fileDocChecker.check_all_docs()
        error = error or info.has_error()
        infos.append(info)
    else:
        for root, dirs, files in os.walk(realpath, topdown=True):
            for name in files:
                if name.endswith(".py"):
                    if name in _EXCLUDES:
                        print "ignoring: " + name
                    else:
                        fileDocChecker = FileDocChecker(os.path.join(root, name), root=realpath)
                        info = fileDocChecker.check_all_docs()
                        error = error or info.has_error()
                        infos.append(info)

            # if "integration_tests" in dirs:
            #    dirs.remove("integration_tests")
            # if "intergration_tests" in dirs:
            #    dirs.remove("intergration_tests")
            # if "unittests" in dirs:
            #     dirs.remove("unittests")
            # if "uinit_test_objects" in dirs:
            #     dirs.remove("uinit_test_objects")
            # Not ready to check
            if ("my_spinnaker") in dirs:
                dirs.remove("my_spinnaker")
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

    print "Writing graphs"
    with open("paths.csv", "w") as file:
        file.write("Class Name,Path\n")
        for info in infos:
            info.add_path_lines(file)
    graph_infos_by_group(ClassInfo.all_classes())
    graph_by_subs(ClassInfo.all_classes())
    # if error:
    #    print "******* ERRORS FOUND **********"
    #    for info in infos:
    #        info.print_errors()
    #    print "******* ERRORS FOUND **********"
    #    sys.exit(1)


if __name__ == "__main__":
    check_directory("../../../")
    #check_directory("exceptions.py")