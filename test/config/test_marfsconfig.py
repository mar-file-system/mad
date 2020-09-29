from config import marfsconfig as cf
import sys
import os
import pytest
import tempfile
import shutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def marfs_config(pytestconfig):
    return pytestconfig.getoption("marfs_config")


@pytest.mark.basic
class TestXMLobj:
    def test_get_just_attrs(self, marfs_config):
        # this test feels worthless
        cfg = cf.MarFSConfig(marfs_config)
        all_stuff = dir(cfg)
        assert all_stuff != cfg.get_just_attrs()

    def test_ensure_strings(self, marfs_config):
        cfg = cf.MarFSConfig(marfs_config)
        p = cfg.hosts.storage_nodes[0].pod
        assert isinstance(p, str)
        cfg.hosts.storage_nodes[0].pod = int(p)
        assert p != cfg.hosts.storage_nodes[0].pod
        cfg.hosts.storage_nodes[0].ensure_strings()
        assert p == cfg.hosts.storage_nodes[0].pod

    @pytest.mark.xfail
    def test_ensure_no_none_fails(self, marfs_config):
        cfg = cf.MarFSConfig(marfs_config)
        cfg.hosts = None
        cfg.ensure_no_none()

    def test_update_attribs(self, marfs_config):
        cfg = cf.MarFSConfig(marfs_config)
        a = cfg.hosts.storage_nodes[0].attribs
        assert a["hostname"] != "something_new"
        cfg.hosts.storage_nodes[0].hostname = "something_new"
        cfg.hosts.storage_nodes[0].update_attribs()
        a = cfg.hosts.storage_nodes[0].attribs
        assert a["hostname"] == "something_new"

    def test_back_to_xml(self, marfs_config):
        # this is hardly comprehensive
        # I can't seem to compare cfg to b
        # without always getting False
        cfg = cf.MarFSConfig(marfs_config)
        temp = tempfile.mkdtemp(dir="/tmp")
        newf = f"{temp}/testout.xml"
        cfg.write_config(newf)
        b = cf.MarFSConfig(newf)
        assert b.config_path != cfg.config_path
        assert b.version == cfg.version
        assert len(b.repos) == len(cfg.repos)
        shutil.rmtree(temp)


class TestMarFSConfig:
    pass


class TestHosts:
    pass
