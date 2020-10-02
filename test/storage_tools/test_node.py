from storage_tools.node import NodeBase
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


@pytest.mark.basic
class TestNodeBase:
    def test_inputs(self, marfs_config, working_repo):
        assert marfs_config
        assert working_repo
        n = NodeBase(marfs_config, working_repo)
        assert n

    def test_valid_host(self, marfs_config, working_repo):
        n = NodeBase(marfs_config, working_repo)
        # localhost is a hostname in the single_node.xml file
        n.fqdn = "localhost"
        assert n.valid_host()
        n.fqdn = "testing.test.fail"
        assert n.hostname == "testing"
        assert not n.valid_host()

    @pytest.mark.xfail
    def test_fail_set_working_repo(self, marfs_config, working_repo):
        n = NodeBase(marfs_config, working_repo)
        assert n
        n = NodeBase(marfs_config, "totally_not_a_repo")

    def test_set_working_repo(self, marfs_config, working_repo):
        n = NodeBase(marfs_config, working_repo)
        assert n

    def test_get_pod_block_caps(self, marfs_config, working_repo):
        n = NodeBase(marfs_config, working_repo)
        n.pod_num = 999
        n.block_num = 999
        caps_paths = n.get_pod_block_caps("/var/tmp")
        for cap in range(int(n.working_repo.data.distribution.caps)):
            assert f"/var/tmp/{n.working_repo.name}/pod{n.pod_num}/" + \
                f"block{n.block_num}/cap{cap}" in caps_paths
