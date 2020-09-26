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


class Node(object):
    def __init__(self, e):
        self.hostname = e.attrib["hostname"]


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
        super().__init__(e)
        self.pod = e.find("pod")
        self.block = e.find("block")

    def to_xml(self, parent):
        #elem = etree.Element()
        p = etree.Element("pod")
        p.text = self.pod
        return p
        
        #print(parent)
        #d.text = self.pod
        #block



class Protection(object):
    def __init__(self, e):
        self.n = e.find("N")
        self.e = e.find("E")
        self.bsz = e.find("BSZ")


class Packing(object):
    def __init__(self, e):
        self.enabled = e.attrib["enabled"]
        self.max_files = e.find("max_files")


class Chunking(object):
    def __init__(self, e):
        self.enabled = e.attrib["enabled"]
        self.max_size = e.find("max_size")


class Distribution(object):
    def __init__(self, e):
        self.pods = e.find("pods")
        self.blocks = e.find("blocks")
        self.caps = e.find("caps")
        self.scatters = e.find("scatters")


class _IO(object):
    def __init__(self, e):
        self.read_size = e.find("read_size")
        self.write_size = e.find("write_size")


class Quota(object):
    def __init__(self, e):
        self.files = e.find("files")
        self.data = e.find("data")


class Permissions(object):
    def __init__(self, e):
        self.interactive = e.find("interactive")
        self.batch = e.find("batch")


class Dal(object):
    def __init__(self, e):
        self.dir_template = e.find("dir_template")
        self.security_root = e.find("security_root")


class Mdal(object):
    def __init__(self, e):
        self.type = e.attrib["type"]
        self.ns_root = e.find("ns_root")
        self.security_root = e.find("security_root")


class Data(object):
    def __init__(self, e):
        self.storage_top = e.find("storage_top")
        self.protection = Protection(e.find("protection"))
        self.packing = Packing(e.find("packing"))
        self.chunking = Chunking(e.find("chunking"))
        self.distribution = Distribution(e.find("distribution"))
        self._io = _IO(e.find("io"))
        self.dal = Dal(e.find("DAL"))


class Metadata(object):
    def __init__(self, e):
        self.namespaces = e.find("namespaces")
        self.namespaces = Namespace(self.namespaces.findall("ns"))
        self.direct_read = e.find("direct").attrib["read"]
        self.direct_write = e.find("direct").attrib["write"]
        self.mdal = Mdal(e.find("MDAL"))


class Namespace(object):
    def __init__(self, e):
        self.name = e.attrib["name"]
        self.quota = Quota(e.find("quota"))
        self.perms = Permissions(e.find("perms"))


class Repo(object):
    def __init__(self, e):
        self.name = e.attrib["name"]
        self.data = Data(e.find("data"))


class Hosts(object):
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

    @property
    def all_hostname(self):
        all_names = []
        all_names.extend([item.hostname for item in self.storage_nodes])
        all_names.extend([item.hostname for item in self.batch_nodes])
        all_names.extend([item.hostname for item in self.interactive_nodes])
        all_names.extend([item.hostname for item in self.metadata_nodes])
        return all_names


class MarFSConfig(object):
    """
    Produces an object with all the keys of our config xml file turned
    into attributes for dot notation.
    Could be useful in interim until final config structs are decided
    Is harder to work with than static
    """
    def __init__(self, config_path=None):
        self.element_tree_root = None
        self.load_config(config_path)
        self.version = self.element_tree_root.attrib["version"]
        self.mnt_top = self.element_tree_root.find("mnt_top")
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
            print("CONFIG: ", config_path)
            self.config_path = config_path
        else:
            config_path = os.environ.get("MARFSCONFIGRC")
            if config_path:
                self.config_path = config_path
            else:
                self.config_path = "/etc/marfsconfig.xml"

        if not os.path.exists(self.config_path):
            sys.exit("could not find config file")

    def create_config_file(self):
        # TODO This should be able to go backwards as well
        pass


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
    print(mcfg.version)
    # for item in mcfg.hosts.storage_nodes:
    #     print(item.hostname)
    e = etree.Element("root")
    e.append(mcfg.hosts.storage_nodes[0].to_xml(e))
    print(e.tostring())