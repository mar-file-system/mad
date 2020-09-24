from storage_tools.interfaces import metadata as mi
import sys
import os
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def working_repo(pytestconfig):
    return pytestconfig.getoption("working_repo")


@pytest.fixture()
def marfs_config(pytestconfig):
    return pytestconfig.getoption("marfs_config")


@pytest.fixture()
def interface_type(pytestconfig):
    return pytestconfig.getoption("mi")


@pytest.mark.skip
class TestMetadataInterface:
    def get_interface(self, marfs_config, working_repo, interface_type):
        interface_type = interface_type.lower().strip()
        if interface_type == "gpfs":
            return mi.GPFSInterface(marfs_config, working_repo)
        else:
            return mi.MetadataInterface(marfs_config, working_repo)

    def test_create_interface(
        self, marfs_config, working_repo, interface_type
    ):
        interface = self.get_interface(
            marfs_config, working_repo, interface_type)
        interface.set_working_repo(working_repo)
        assert interface

    def test_enough_scatters(self, marfs_config, working_repo, interface_type):
        # TODO update this
        # Seems more like a deployment test??
        SNT = self.get_interface(marfs_config, working_repo, interface_type)
        SNT.set_working_repo(working_repo)
        assert SNT
        # num_scatters = int(SNT.working_repo.dal.scatter_width)
        # pattern = SNT.working_repo.host.split("/")[-1]
        # pattern = pattern.replace("%d", "%s")
        # caps = [item[4] for item in data]
        # for cap in caps:
        #     dirs = os.listdir(cap)
        #     dirs = [directory for directory in dirs if pattern in directory]
        #     assert len(dirs) == num_scatters


@pytest.mark.cluster
class TestGPFSInterface:
    # TODO start making this work
    def get_interface(self, marfs_config, working_repo):
        return mi.GPFSInterface(marfs_config, working_repo)
