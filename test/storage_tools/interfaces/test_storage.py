import sys
import os
import pytest
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage_tools.interfaces import storage as si


@pytest.fixture()
def working_repo(pytestconfig):
    return pytestconfig.getoption("working_repo")

@pytest.fixture()
def marfs_config(pytestconfig):
    return pytestconfig.getoption("marfs_config")


@pytest.mark.basic
class TestStorageInterface:
    def test_create_storage_interface(self, marfs_config, working_repo):
        i = si.StorageInterface(marfs_config, working_repo)
        i.set_working_repo(working_repo)
        assert i

    def test_create_pod_block_cap_scatter(self, marfs_config, working_repo):
        i = si.StorageInterface(marfs_config, working_repo)
        p = i.working_repo.host.split("/")[-1].replace("%d", "%s")
        cap_paths = i.get_pod_block_caps(i.config.storage_top)
        for path in cap_paths:
            assert not os.path.isdir(path)
        i.create_pod_block_cap_scatter()
        for path in cap_paths:
            assert os.path.isdir(path)
            shutil.rmtree(path)


    def test_load_config_data(self, marfs_config, working_repo):
        i = si.StorageInterface(marfs_config, working_repo)
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

