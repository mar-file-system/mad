# Copyright(c) 2015, Los Alamos National Security, LLC
# All rights reserved.

# Copyright 2015.  Los Alamos National Security, LLC. This software was
# produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos
# National Laboratory(LANL), which is operated by Los Alamos National
# Security, LLC for the U.S. Department of Energy. The U.S. Government has
# rights to use, reproduce, and distribute this software.  NEITHER THE
# GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY, EXPRESS
# OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If
# software is modified to produce derivative works, such modified software
# should be clearly marked, so as not to confuse it with the version available
# from LANL.

# Additionally, redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of Los Alamos National Security, LLC, Los Alamos
# National Laboratory, LANL, the U.S. Government, nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL
# SECURITY, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES(INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA,
# OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT(INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -----
# NOTE:
# -----
# MarFS is released under the BSD license.

# MarFS was reviewed and released by LANL under Los Alamos Computer Code
# identifier: LA-CC-15-039.

# MarFS uses libaws4c for Amazon S3 object communication. The original version
# is at https://aws.amazon.com/code/Amazon-S3/2601 and under the LGPL license.
# LANL added functionality to the original work. The original work plus
# LANL contributions is found at https: // github.com/jti-lanl/aws4c.

# GNU licenses can be found at http: // www.gnu.org/licenses/.

import sys
import os
from lxml import etree


class XMLobj(object):
    def __init__(self, element, lazy=False):
        self.elem = element
        self.e_name = element.tag
        self.attribs = element.attrib
        self.ensure_no_none()

    def get_just_attrs(self):
        things = dir(self)
        excludes = ["e_name", "elem", "all_hostnames", "comments"]
        things = [t for t in things if "__" not in t]
        things = [t for t in things if not callable(
            self.__getattribute__(t))]
        things = [t for t in things if not isinstance(
            self.__getattribute__(t), etree._Attrib)]
        things = [t for t in things if t not in self.attribs.keys()]
        things = [t for t in things if t not in excludes]
        return things

    def ensure_strings(self):
        things = self.get_just_attrs()
        for thing in things:
            attrval = self.__getattribute__(thing)
            if isinstance(attrval, dict):
                pass
            if isinstance(attrval, int):
                setattr(self, thing, str(attrval))
            if isinstance(attrval, float):
                setattr(self, thing, str(attrval))

    def ensure_no_none(self):
        things = self.get_just_attrs()
        for thing in things:
            attrval = self.__getattribute__(thing)
            if attrval is None:
                print("\nERROR IN TAG:", thing, "\n")
                sys.exit("Can't have empty values in config")

    def update_attribs(self):
        attribs = self.__getattribute__("attribs")
        for thing in attribs:
            if thing in self.attribs.keys():
                if self.__getattribute__(thing) != self.attribs[thing]:
                    self.attribs[thing] = self.__getattribute__(thing)

    def back_to_xml(self, parent):
        self.ensure_strings()
        things = self.get_just_attrs()
        self.update_attribs()
        elem = etree.SubElement(parent, self.e_name, self.attribs)
        for thing in things:
            item = self.__getattribute__(thing)
            if isinstance(item, str):
                etree.SubElement(elem, thing).text = item
            elif isinstance(item, list):
                for i in item:
                    i.back_to_xml(elem)
            else:
                if item:
                    item.back_to_xml(elem)


class Node(XMLobj):
    def __init__(self, e):
        self.hostname = e.attrib["hostname"]
        super().__init__(e)


class BatchNode(Node):
    def __init__(self, e):
        super().__init__(e)


class MetadataNode(Node):
    def __init__(self, e):
        super().__init__(e)


class InteractiveNode(Node):
    def __init__(self, e):
        super().__init__(e)


class StorageNode(Node):
    def __init__(self, e):
        self.pod = e.find("pod").text
        self.block = e.find("block").text
        super().__init__(e)


class Protection(XMLobj):
    def __init__(self, e):
        self.N = e.find("N").text
        self.E = e.find("E").text
        self.BSZ = e.find("BSZ").text
        super().__init__(e)


class Packing(XMLobj):
    def __init__(self, e):
        self.enabled = e.attrib["enabled"]
        self.max_files = e.find("max_files").text
        super().__init__(e)


class Chunking(XMLobj):
    def __init__(self, e):
        self.enabled = e.attrib["enabled"]
        self.max_size = e.find("max_size").text
        super().__init__(e)


class Distribution(XMLobj):
    def __init__(self, e):
        self.pods = e.find("pods").text
        self.blocks = e.find("blocks").text
        self.caps = e.find("caps").text
        self.scatters = e.find("scatters").text
        super().__init__(e)


class _IO(XMLobj):
    def __init__(self, e):
        self.read_size = e.find("read_size").text
        self.write_size = e.find("write_size").text
        super().__init__(e)


class Quota(XMLobj):
    def __init__(self, e):
        self.files = e.find("files").text
        self.data = e.find("data").text
        super().__init__(e)


class Permissions(XMLobj):
    def __init__(self, e):
        self.interactive = e.find("interactive").text
        self.batch = e.find("batch").text
        super().__init__(e)


class Direct(XMLobj):
    def __init__(self, e):
        self.read = e.attrib["read"]
        self.write = e.attrib["write"]
        super().__init__(e)


class Dal(XMLobj):
    def __init__(self, e):
        self.type = e.attrib["type"]
        self.dir_template = e.find("dir_template").text
        self.security_root = e.find("security_root").text
        super().__init__(e)


class Mdal(XMLobj):
    def __init__(self, e):
        self.type = e.attrib["type"]
        self.ns_root = e.find("ns_root").text
        self.security_root = e.find("security_root").text
        super().__init__(e)


class Data(XMLobj):
    def __init__(self, e):
        self.storage_top = e.find("storage_top").text
        self.protection = Protection(e.find("protection"))
        self.packing = Packing(e.find("packing"))
        self.chunking = Chunking(e.find("chunking"))
        self.distribution = Distribution(e.find("distribution"))
        self._io = _IO(e.find("io"))
        self.dal = Dal(e.find("DAL"))
        super().__init__(e)


class Metadata(XMLobj):
    def __init__(self, e):
        self.namespaces = [
            Namespace(item) for item in e.findall("ns")
        ]
        self.mdal = Mdal(e.find("MDAL"))
        self.direct = Direct(e.find("direct"))
        super().__init__(e)


class Namespace(XMLobj):
    def __init__(self, e):
        self.name = e.attrib["name"]
        self.quota = Quota(e.find("quota"))
        self.perms = Permissions(e.find("perms"))
        super().__init__(e)


class Repo(XMLobj):
    def __init__(self, e):
        self.name = e.attrib["name"]
        self.data = Data(e.find("data"))
        self.metadata = Metadata(e.find("metadata"))
        super().__init__(e)


class Hosts(XMLobj):
    def __init__(self, e):
        self.storage_nodes = [
            StorageNode(item) for item in e.findall("storage_node")
        ]
        self.batch_nodes = [
            BatchNode(item) for item in e.findall("batch_node")
        ]
        self.interactive_nodes = [
            InteractiveNode(item) for item in e.findall("interactive_node")
        ]
        self.metadata_nodes = [
            MetadataNode(item) for item in e.findall("metadata_node")
        ]
        super().__init__(e)

    @property
    def all_hostnames(self):
        all_names = []
        all_names.extend([item.hostname for item in self.storage_nodes])
        all_names.extend([item.hostname for item in self.batch_nodes])
        all_names.extend([item.hostname for item in self.interactive_nodes])
        all_names.extend([item.hostname for item in self.metadata_nodes])
        return all_names


class MarFSConfig(XMLobj):
    """
    Produces an object with all the keys of our config xml file turned
    into attributes for dot notation.
    Could be useful in interim until final config structs are decided
    Is harder to work with than static
    """
    def __init__(self, config_path=None):
        self.element_tree_root = None
        self.load_config(config_path)
        super().__init__(self.element_tree_root)
        self.version = self.element_tree_root.attrib["version"]
        self.mnt_top = self.element_tree_root.find("mnt_top").text
        self.hosts = Hosts(self.element_tree_root.find("hosts"))
        self.repos = [Repo(item)
                      for item in self.element_tree_root.findall("repo")]

    def load_config(self, config_path):
        self.get_config_path(config_path)

        with open(self.config_path) as fp:
            data = etree.parse(fp)
        if data:
            self.element_tree_root = data.getroot()
        else:
            sys.exit("Error: empty config")

    def get_config_path(self, config_path):
        if config_path:
            print("CONFIG:", config_path)
            self.config_path = config_path
        else:
            config_path = os.environ.get("MARFSCONFIGRC")
            if config_path:
                self.config_path = config_path
            else:
                self.config_path = "/etc/marfsconfig.xml"

        if not os.path.exists(self.config_path):
            sys.exit("could not find config file")

    def to_xml(self):
        elem = etree.Element("marfs_config", version=self.version)
        etree.SubElement(elem, "mnt_top").text = self.mnt_top
        self.hosts.back_to_xml(elem)
        for repo in self.repos:
            repo.back_to_xml(elem)

        return elem

    def write_config(self, outf=None):
        if not outf:
            outf = self.config_path
        xml = self.to_xml()
        fp = open(outf, "w")
        fp.write(etree.tostring(
            xml,
            pretty_print=True,
            xml_declaration=True,
            with_comments=True,
            encoding="utf-8").decode("utf-8")
        )
        fp.close()


class ConfigTool(object):
    """
    Used to manipulate config file
    Most tools that add to the config file can't be done yet
    Once config struct is final that can be done
    """
    # TODO need to do this
    def __init__(self):
        pass

    def new_repo(self, setup=False):
        """
        Add a repo to the config file
        """
        pass

    def new_namespace(self, setup=False):
        """
        Add a namespace to the config file
        """
        pass


if __name__ == '__main__':
    mcfg = MarFSConfig("new_config.xml")
    mcfg.write_config("testout.xml")
