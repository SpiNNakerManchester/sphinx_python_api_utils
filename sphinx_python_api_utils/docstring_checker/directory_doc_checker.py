import os
from subprocess import call

from file_doc_checker import FileDocChecker
import class_info as class_info

_EXCLUDES = ["va_benchmark.py"]
_OK_EXCLUDES = ["setup.py"]


def find_groups_up_and_down(info, found):
    if info in found:
        return
    found.add(info)
    for super in info.supers:
        find_groups_up_and_down(super, found)
    if info.state > class_info.STATELESS:
        for user in info.users:
            find_groups_up_and_down(user, found)


def find_groups_up(info, found, base):
    if info in found:
        if base is not None:
            print "Diamond found over: {}".format(base.name)
        return
    found.add(info)
    for user in info.users:
        find_groups_up(user, found, base)


def graph(infos, name):
    gv_name = name + ".gv"
    png_name = name + ".png"
    with open(gv_name, "w") as file:
        n_count = 0
        file.write("digraph G {\n")
        for info in infos:
            n_count = info.add_graph_lines(file, n_count)
        file.write("}")
    call(["dot", "-Tpng", gv_name, "-o", png_name])


def graph_infos_by_group(infos):
    graph_count = 0
    while len(infos) > 0:
        info = infos[0]
        if ((len(info.supers)) == 0 and (len(info.users) == 0)) or \
                (info.state <= class_info.STATELESS):
            infos.remove(info)
        else:
            info_group = set()
            find_groups_up_and_down(info, info_group)
            graph_count += 1
            graph(info_group, "supers/graph{}".format(graph_count))
            for gr_info in info_group:
                if gr_info in infos:
                    infos.remove(gr_info)
#            find_diamond(gr_info)


def graph_by_super(info):
    info_group = set()
    if info.state > class_info.STATELESS:
        base = info
    else:
        base = None
    find_groups_up(info, info_group, base)
    if (len(info_group) >= 2):
        graph(info_group, "supers/" + info.name)


def graph_by_supers(infos):
    for info in infos:
        if len(info.users) > 0:
            graph_by_super(info)


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
                    elif name in _OK_EXCLUDES:
                        pass
                    else:
                        fileDocChecker = FileDocChecker(
                            os.path.join(root, name), root=realpath)
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
    graph_infos_by_group(class_info.ClassInfo.all_classes())
    graph_by_supers(class_info.ClassInfo.all_classes())
    # if error:
    #    print "******* ERRORS FOUND **********"
    #    for info in infos:
    #        info.print_errors()
    #    print "******* ERRORS FOUND **********"
    #    sys.exit(1)


if __name__ == "__main__":
    check_directory("../../../")
    # check_directory("exceptions.py")
