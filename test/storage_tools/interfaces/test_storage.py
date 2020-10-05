from storage_tools.interfaces import storage as si
import sys
import os
import pytest
import shutil
import tempfile

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
@pytest.mark.zfs
class TestZFSInterface:
    def get_storage_interface(self, marfs_config, working_repo):
        return si.ZFSInterface(marfs_config, working_repo)

    def test_get_disks(self, marfs_config, working_repo):
        i = self.get_storage_interface(marfs_config, working_repo)
        disks = i.get_disks()
        for disk in disks:
            assert "enclosure" not in disk
            assert "process" not in disk
        # should test all disks are in same enclosure
        # but can't because we don't have an enclosure variable input

    @pytest.mark.skip
    def test_set_pool_opts(self, marfs_config, working_repo):
        """
        Not sure we can test this without messing with a pool
        """
        pass

    def test_get_pools(self, marfs_config, working_repo):
        pass

    def test_create_datastore(self, marfs_config, working_repo):
        i = self.get_storage_interface(marfs_config, working_repo)
        pools = i.get_pools()
        pool = pools[0][0]
        i.create_datastore(pool, "testing_datastore")
        datastores = i.get_datastores()
        found = False
        for ds in datastores:
            if "testing_datastore" in ds[0]:
                found = True
        assert found
    @pytest.mark.skip
    def test_mount_datastore(self, marfs_config, working_repo):
        i = self.get_storage_interface(marfs_config, working_repo)
        for ds in i.get_datastores():
            if "testing_datastore" in ds[0]:
                datastore = ds[0]
        temp = tempfile.mkdtemp(dir="/tmp")
        i.mount_datastore(datastore, temp)
        i.run(f"zfs list {temp}")
        assert i.last_command.stderr == 0

    def test_unmount_datastore(self, marfs_config, working_repo):
        # too straight forward to need a test?
        pass

    def test_get_datastores(self, marfs_config, working_repo):
        i = self.get_storage_interface(marfs_config, working_repo)
        assert i.get_datastores()


@pytest.mark.skip
class TestZFSSetup:
    def test_setup_zfs(self, marfs_config, working_repo):
        # TODO This is a test that would only
        # work on a totally isolated system
        pass

    def test_unmount_all_datastores(self, marfs_config, working_repo):
        # This seems like a risky test maybe skip?
        # Or only test on isolated deployment
        # TODO only test on pre-prod systems
        pass

    def test_make_all_datastores(self, marfs_config, working_repo):
        # TODO This seems like a deployment test
        pass

    def test_mount_all_datastores(self, marfs_config, working_repo):
        # TODO This seems like a deploylemnt test
        pass

    def test_create_zpool(self, marfs_config, working_repo):
        # TODO I'm not certain we can acutally unit test zpool stuff
        # without being on a isolated system where it won't hurt
        pass

    def test_deploy_repo(self, marfs_config, working_repo):
        # TODO This should be covered by deployment tests
        pass
