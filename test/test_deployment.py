from src.interfaces.storage import ZFSInterface
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


@pytest.mark.zfsdeployment
class TestStorageDeployment:

    def test_marfs_config_set(self, marfs_config):
        # TODO this needs to be updated and fixed
        assert os.path.exists(marfs_config)

    def test_check_zfs_ready(self, marfs_config, working_repo):
        i = self.get_storage_node_tools(marfs_config, working_repo)
        assert i.check_zfs_ready()

    def test_enough_scatters(self, marfs_config, working_repo):
        SNT = self.get_storage_node_tools(marfs_config, working_repo)
        SNT.set_working_repo(working_repo)
        num_scatters = int(SNT.working_repo.data.distribution.scatters)
        pattern = SNT.working_repo.data.dal.dir_template.split("/")[-1]
        pattern = pattern.replace("%d", "")
        data = SNT.get_datastores()
        assert data
        caps = [item[4] for item in data]
        for cap in caps:
            dirs = os.listdir(cap)
            dirs = [directory for directory in dirs if pattern in directory]
            assert len(dirs) >= num_scatters

    def test_are_there_zpools(self, marfs_config, working_repo):
        SNT = self.get_storage_node_tools(marfs_config, working_repo)
        assert SNT.get_pools()

    def are_zpools_raidz3(self):
        SNT = ZFSInterface("tests")
        for zpool in SNT.get_pools():
            SNT.run(f"zpool status -v {zpool}")
        assert "raidz3" in SNT.plist[-1].stdout.decode("utf-8").lower()

    def test_check_zfs_nfs(self, marfs_config, working_repo):
        SNT = self.get_storage_node_tools(marfs_config, working_repo)
        cmd = f"zfs list {SNT.working_repo.data.storage_top}"
        SNT.run(cmd)
        assert SNT.last_command.returncode == 0

    def test_are_there_zfs_datasets(self, marfs_config, working_repo):
        SNT = self.get_storage_node_tools(marfs_config, working_repo)
        assert SNT.get_datastores()

    def test_check_dataset_count(self, marfs_config, working_repo):
        SNT = self.get_storage_node_tools(marfs_config, working_repo)
        SNT.set_working_repo(working_repo)
        data = SNT.get_datastores()
        assert len(data) >= int(SNT.working_repo.data.distribution.caps)

    def test_check_dataset_mounts(self, marfs_config, working_repo):
        SNT = self.get_storage_node_tools(marfs_config, working_repo)
        data = SNT.get_datastores()
        SNT.set_working_repo(working_repo)
        for dataset in data:
            dataset_name = dataset[0]
            dataset_mountpoint = dataset[4]
            cmd = f"zfs list {dataset_name}"
            SNT.run(cmd)
            assert SNT.last_command.returncode == 0
            assert os.path.exists(dataset_mountpoint)

    def get_storage_node_tools(self, marfs_config, working_repo):
        return ZFSInterface(marfs_config, working_repo)
