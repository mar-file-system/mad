from storage_tools.interfaces import storage as si
import sys
import os
import pytest
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def working_repo(pytestconfig):
    return pytestconfig.getoption("working_repo")


@pytest.fixture()
def marfs_config(pytestconfig):
    return pytestconfig.getoption("marfs_config")


@pytest.fixture()
def interface_type(pytestconfig):
    return pytestconfig.getoption("si")


@pytest.mark.basic
class TestStorageInterface:
    def get_interface(self, marfs_config, working_repo, interface_type):
        interface_type = interface_type.lower().strip()
        if interface_type == "zfs":
            return si.ZFSInterface(marfs_config, working_repo)
        else:
            return si.StorageInterface(marfs_config, working_repo)

    def test_create_storage_interface(
        self, marfs_config, working_repo, interface_type
    ):
        i = self.get_interface(marfs_config, working_repo, interface_type)
        i.set_working_repo(working_repo)
        assert i

    def test_create_pod_block_cap_scatter(
        self, marfs_config, working_repo, interface_type
    ):
        i = self.get_interface(marfs_config, working_repo, interface_type)
        cap_paths = i.get_pod_block_caps(i.working_repo.data.storage_top)
        for path in cap_paths:
            assert not os.path.isdir(path)
        i.create_pod_block_cap_scatter()
        for path in cap_paths:
            assert os.path.isdir(path)
            shutil.rmtree(path)

    def test_load_config_data(
        self, marfs_config, working_repo, interface_type
    ):
        i = self.get_interface(marfs_config, working_repo, interface_type)
        i.pod_num = None
        i.block_num = None
        assert i.pod_num is None
        assert i.block_num is None
        # This should set the pod and block to
        # the first storage node in the config
        # which using my brain would be pod 0 block 0
        i._trick_valid_host()
        assert int(i.pod_num) == 0
        assert int(i.block_num) == 0


@pytest.mark.cluster
class TestZFSInterface:
    def get_storage_interface(self, marfs_config, working_repo):
        return si.ZFSInterface(marfs_config, working_repo)
