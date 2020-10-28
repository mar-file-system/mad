from src.interfaces import metadata as mi
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
    return pytestconfig.getoption("mi")


@pytest.mark.basic
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
        i = self.get_interface(marfs_config, working_repo, interface_type)
        i.set_working_repo(working_repo)
        assert i

    def test_create_pod_block_caps(
        self, marfs_config, working_repo, interface_type
    ):
        i = self.get_interface(marfs_config, working_repo, interface_type)
        i.create_pod_block_caps()
        pods = range(int(i.working_repo.data.distribution.pods))
        blocks = range(int(i.working_repo.data.distribution.blocks))
        ns_root = i.working_repo.metadata.mdal.ns_root
        for p in pods:
            i.pod_num = p
            for b in blocks:
                i.block_num = b
                caps = i.get_pod_block_caps(ns_root)
                assert len(caps) == int(
                    i.working_repo.data.distribution.caps)
                for cap in caps:
                    assert os.path.isdir(cap)
                    shutil.rmtree(cap)


@pytest.mark.skip
class TestGPFSInterface:
    # TODO The only methods here amount to making directories
    # So they will only be tested in a deployment test
    def get_interface(self, marfs_config, working_repo):
        return mi.GPFSInterface(marfs_config, working_repo)
