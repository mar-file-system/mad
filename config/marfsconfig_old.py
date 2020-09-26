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


class QuickObject(object):
    def __init__(self, etree_element):
        for child in etree_element.getchildren():
            if len(child) == 0:
                setattr(self, child.tag, child.text)


class Node(QuickObject):
    def __init__(self, element_tree):
        # Forward declarations
        self.hostname = None
        super().__init__(element_tree)


class FtaNode(Node):
    def __init__(self, element_tree):
        super().__init__(element_tree)


class MetaDataNode(Node):
    def __init__(self, element_tree):
        super().__init__(element_tree)


class IntNode(Node):
    def __init__(self, element_tree):
        super().__init__(element_tree)


class StorageNode(QuickObject):
    def __init__(self, element_tree):
        # Forward declarations
        self.hostname = None
        self.pod = None
        self.block = None
        super().__init__(element_tree)


class Dal(QuickObject):
    def __init__(self, element_tree):
        # Forward declarations
        self.type = None
        self.n = None
        self.e = None
        self.pods = None
        self.blocks = None
        self.caps = None
        self.scatter_width = None
        self.degraded_log_dir = None
        super().__init__(element_tree)


class Namespace(QuickObject):
    def __init__(self, element_tree):
        # Forward declarations
        self.id = None
        self.name = None
        self.mnt_path = None
        self.bperms = None
        self.iperms = None
        self.min_size = None
        self.max_size = None
        self.md_path = None
        self.trash_md_path = None
        self.fsinfo_path = None
        self.quota_space = None
        self.quota_names = None
        super().__init__(element_tree)


class Repo(QuickObject):
    def __init__(self, repo_element_tree):
        # Forward declarations
        self.name = None
        self.host = None
        self.host_offset = None
        self.host_count = None
        self.update_in_place = None
        self.ssl = None
        self.access_method = None
        self.chunk_size = None
        self.max_pack_file_count = None
        self.min_pack_file_count = None
        self.max_pack_file_size = None
        self.min_pack_file_size = None
        self.latency = None
        self.timing_flags = None
        self.dal = None
        super().__init__(repo_element_tree)
        self.dal = Dal(repo_element_tree.find("dal"))
        self.namespaces = [
            Namespace(item) for item in repo_element_tree.findall("namespace")
            ]


class LazyConfig(QuickObject):
    """
    Produces an object with all the keys of our config xml file turned
    into attributes for dot notation.
    Could be useful in interim until final config structs are decided
    Is harder to work with than static
    """
    def __init__(self, config_path=None):
        # Forward declarations
        self.name = None
        self.version = None
        self.mnt_top = None
        self.mdfs_top = None
        self.storage_top = None
        self.repos = None
        self.storage_nodes = None
        self.fta_nodes = None
        self.int_nodes = None
        self.metadata_nodes = None
        self.all_hosts = None
        self.load_config(config_path)

    def load_config(self, config_path):
        self.get_config_path(config_path)

        with open(self.config_path) as fp:
            data = etree.parse(fp)
        if data:
            data = data.getroot()
            super().__init__(data)
            self.repos = [Repo(item) for item in data.findall("repo")]
            self.storage_nodes = [
                StorageNode(item) for item in data.findall("storage_node")
                ]
            self.fta_nodes = [
                FtaNode(item) for item in data.findall("fta_node")
                ]
            self.metadata_nodes = [
                MetaDataNode(item) for item in data.findall("metadata_node")
                ]
            self.int_nodes = [Node(item) for item in data.findall("int_node")]
            self.all_hosts = self.storage_nodes + self.fta_nodes + \
                self.metadata_nodes + self.int_nodes
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


class MarfsConfig(object):
    def __init__(self, config_path=None):
        pass

    def load_config(self, config_path):
        self.get_config_path(config_path)

        with open(self.config_path) as fp:
            data = etree.parse(fp)
        if data:
            data = data.getroot()
            super().__init__(data)
            self.repos = [Repo(item) for item in data.findall("repo")]
            self.storage_nodes = [
                StorageNode(item) for item in data.findall("storage_node")
            ]
            self.fta_nodes = [
                FtaNode(item) for item in data.findall("fta_node")
            ]
            self.metadata_nodes = [
                MetaDataNode(item) for item in data.findall("metadata_node")
            ]
            self.int_nodes = [Node(item) for item in data.findall("int_node")]
            self.all_hosts = self.storage_nodes + self.fta_nodes + \
                self.metadata_nodes + self.int_nodes
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
    mcfg = LazyConfig("config.xml")
