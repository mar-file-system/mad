import sys
import os
from lxml import etree


def get_namespace(element_tree, repo_name):
    pass


def update_namespace(namespace_name):
    pass


def new_namespace(namespace_name, quota_files, quota_data, iperms, bperms):
    pass


def get_repo(element_tree):
    pass

def testing():
    from lxml import etree
    with open("test_file_out.xml", "r") as fp:
        data = etree.parse(fp)

    data = data.getroot()

    for item in data:
        if item.tag == "repo":
            if item.attrib["name"] == "testone":
                item.attrib["name"] = "testchange"

    with open("test_file_out.xml", "w") as fp:
        fp.write(etree.tostring(data).decode("utf-8"))


if __name__ == '__main__':
    testing()
