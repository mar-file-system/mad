# conftest.py
import os


def pytest_addoption(parser):
    def_config = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    def_config = def_config + "/config/tests.xml"
    def_repo = "single"
    # def_storage_interface = "storage_interface"
    # def_metadata_interface = "metadata_interface"

    parser.addoption("--working_repo", action="store", default=def_repo)
    # TODO config should default to none in the future.
    # This is just laziness for testing.
    parser.addoption("--marfs_config", action="store", default=def_config)
