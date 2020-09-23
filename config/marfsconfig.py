import sys
import os
from lxml import etree
from typing import Optional, List
import json


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
        self.namespaces = [Namespace(item) for item in repo_element_tree.findall("namespace")]

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
            self.repos = [ Repo(item) for item in data.findall("repo") ]
            self.storage_nodes = [ StorageNode(item) for item in data.findall("storage_node") ]
            self.fta_nodes = [ FtaNode(item) for item in data.findall("fta_node") ]
            self.metadata_nodes = [ MetaDataNode(item) for item in data.findall("metadata_node") ]
            self.int_nodes = [ Node(item) for item in data.findall("int_node") ]
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


class NodesConf(object):
    pass

class MaraadConfig(object):
    """
    This currently does nothing, use LazyConfig until config is final for MARFS
    """
    def __init__(self, config : Optional[str]) -> None:
        self.conf_path = config
        self.pods = []
        self.ftas = []
        self.gpfs = []
        self.int_nodes = []
        self.load_config()

    def load_config(self) -> None:
        self.get_conf_path()

        with open(self.conf_path) as fp:
            data = json.load(fp)
        if data:
            self.set_nodes_from_dict(data)

    def get_conf_path(self) -> None:
        if self.conf_path:
            pass
        else:
            conf_path = os.environ.get("MARAADCFG")
            if conf_path:
                self.conf_path = conf_path
            else:
                self.conf_path = "/etc/maraad.json"
    
    def set_nodes_from_dict(self, data: dict) -> None:
        self.pods = data["pods"]
        self.ftas = data["ftas"]
        self.gpfs = data["gpfs"]
        self.int_nodes = data["int_nodes"]

    def create_config(self) -> None:
        
        pass





if __name__ == '__main__':
    mcfg = LazyConfig("config.xml")
    

