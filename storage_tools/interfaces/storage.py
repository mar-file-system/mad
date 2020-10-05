# Copyright(c) 2015, Los Alamos National Security, LLC
# All rights reserved.

# Copyright 2015.  Los Alamos National Security, LLC. This software was
# produced under U.S. Government contract DE-AC52-06NA25396 for Los Alamos
# National Laboratory(LANL), which is operated by Los Alamos National
# Security, LLC for the U.S. Department of Energy. The U.S. Government has
# rights to use, reproduce, and distribute this software.  NEITHER THE
# GOVERNMENT NOR LOS ALAMOS NATIONAL SECURITY, LLC MAKES ANY WARRANTY, EXPRESS
# OR IMPLIED, OR ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If
# software is modified to produce derivative works, such modified software
# should be clearly marked, so as not to confuse it with the version available
# from LANL.

# Additionally, redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of Los Alamos National Security, LLC, Los Alamos
# National Laboratory, LANL, the U.S. Government, nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL
# SECURITY, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES(INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES LOSS OF USE, DATA,
# OR PROFITS OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT(INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -----
# NOTE:
# -----
# MarFS is released under the BSD license.

# MarFS was reviewed and released by LANL under Los Alamos Computer Code
# identifier: LA-CC-15-039.

# MarFS uses libaws4c for Amazon S3 object communication. The original version
# is at https://aws.amazon.com/code/Amazon-S3/2601 and under the LGPL license.
# LANL added functionality to the original work. The original work plus
# LANL contributions is found at https: // github.com/jti-lanl/aws4c.

# GNU licenses can be found at http: // www.gnu.org/licenses/.

from storage_tools.node import NodeBase
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class StorageInterface(NodeBase):
    def __init__(self, marfs_config=None, marfs_repo=None):
        super().__init__(marfs_config, marfs_repo)
        self.load_config_data()

    def _trick_valid_host(self):
        self.fqdn = self.config.hosts.storage_nodes[0].hostname
        self.valid = self.valid_host()
        self.load_config_data()

    def load_config_data(self):
        """
        Some data needs to be loaded from the config file specific to a host
        so we get those values from the config and set them here
        """
        hostnames = [self.fqdn, self.hostname]
        if self.valid:
            for hostname in hostnames:
                for host in self.config.hosts.storage_nodes:
                    if host.hostname == hostname:
                        self.pod_num = host.pod
                        self.block_num = host.block
                if self.pod_num:
                    break

    def create_pod_block_cap_scatter(self):
        scatter_size = int(self.working_repo.data.distribution.scatters) + 1
        scatter_t = self.working_repo.data.dal.dir_template.split("/")[-1]
        scatter_t.replace("%d", "%s")
        caps = self.get_pod_block_caps(self.working_repo.data.storage_top)

        for pbc_path in caps:
            for i in range(scatter_size):
                os.makedirs(pbc_path + "/" + scatter_t % i, exist_ok=True)

    def deploy_repo(self, repo_name):
        self.set_working_repo(repo_name)
        self.create_pod_block_cap_scatter()


class ZFSInterface(StorageInterface):
    def __init__(
        self, marfs_config=None, marfs_repo=None, jbod="1"
    ):
        print("ZFS storage interface")
        self.jbod = str(jbod)
        super().__init__(marfs_config, marfs_repo)

    def get_disks(self):
        """
        ZFSTOOL
        Gets all disk paths in an enclosure
        """
        self.run("lsscsi")
        output = self.plist[-1].stdout.decode('utf-8').strip().split("\n")
        output = [item for item in output if "process" not in item]
        for item in output:
            if "enclos" in item:
                enclosure = item

        if not enclosure:
            sys.exit("No enclosure present")

        enclosure_info = enclosure.split()[0][1:-1].split(":")
        disks = []
        for item in output:
            points = item.split()
            scsi_data = points[0][1:-1].split(":")
            if "enclosu" not in item:
                if str(scsi_data[0]) == str(enclosure_info[0]):
                    disks.append(points[-1])

        return disks

    def start_zfs(self):
        """
        ZFSTOOL
        Try to start ZFS services and import zpools
        """
        self.run("systemctl restart storage-start")

    def set_pool_opts(self, pool_name):
        cmds = [
            f"zfs set mountpoint=none {pool_name}",
            f"zfs set recordsize=1M {pool_name}",
            f"zfs set compression=lz4 {pool_name}",
            f"zfs set atime=off {pool_name}"
        ]

        for cmd in cmds:
            self.run(cmd)

    # POOL METHODS
    def pools_up(self):
        """
        ZFSTOOL
        """
        if self.get_pools():
            return True
        else:
            return False

    def get_pools(self):
        """
        Get a list of pools
        """
        cmd = "zpool list"
        self.run(cmd)
        p = self.plist[-1]
        if not p.stderr:
            data = p.stdout.decode('utf-8').strip().split("\n")
            data = [item.split() for item in data]
            if data:
                # return only pools, no headers
                return data[1:]
            else:
                return None
        else:
            return None

    def create_zpool(self, pool_name, disks, force_zpools):
        if force_zpools:
            cmd = f'zpool create -f {pool_name} raidz3 {disks}'
        else:
            cmd = f'zpool create {pool_name} raidz3 {disks}'
        self.run(cmd, timeout=None)

    def make_pools(self, force_zpools):
        """
        ZFSTOOL
        """

        disks = self.get_disks()
        disk_pools = {}
        for i in range(int(self.working_repo.dal.caps)):
            disk_pools[str(i)] = disks[i*20:(i+1)*20]
        print(disk_pools)

        for pool_num in disk_pools.keys():
            pool_t = f"{self.hostname}-jbod{self.jbod}-pool{pool_num}"
            print(pool_t)
            add_disks = " ".join(disk_pools[pool_num])
            self.create_zpool(pool_t, add_disks, force_zpools)
            print(self.plist[-1])
            print(add_disks)
            self.set_pool_opts(pool_t)

    # DATASTORE METHODS
    def create_datastore(self, pool, datastore_name):
        """
        Creates a datastore on pool with name datastore_name
        ex pool0/datatore
        """
        cmd = f'zfs create {pool}/{datastore_name}'
        self.run(cmd)

    def mount_datastore(self, datastore, mount_path):
        """
        ZFSTOOL
        TODO rework this method
        """
        cmd = f"zfs set mountpoint={mount_path} {datastore}"
        if os.path.isdir(mount_path):
            if os.listdir(mount_path):
                sys.exit(f"{mount_path} not empty")
        self.run(cmd)

    def unmount_datastore(self, datastore):
        cmd = f"zfs set mountpoint=none {datastore}"
        self.run(cmd)

    def get_datastores(self, datastore_name="datastore"):
        """
        similar to get pools
        Should zfs list and pick out datastores
        Should ignore nfs datastore
        Should filter out pools
        """
        cmd = "zfs list"
        self.run(cmd)
        p = self.plist[-1]
        if not p.stderr:
            data = p.stdout.decode('utf-8').strip().split("\n")
            data = [item.split() for item in data]
            # drop pools and NFS datastores
            data = [item for item in data if "/" in item[0]
                    and "nfs" not in item[0]]
            data = [item for item in data if f"jbod{self.jbod}" in item[0]]
            data = [item for item in data if datastore_name in item[0]]
            if data:
                return data
            else:
                return None
        else:
            return None
        pass

    def make_zfs_nfs(self, pool_name=None):
        """
        Creates the NFS datastore on a pool
        default pool is the first listed
        """
        if not pool_name:
            pools = self.get_pools()
            pool_name = pools[0][0]

        cmd = f"zfs create {pool_name}/nfs " + \
            f"-o mountpoint={self.working_repo.data.storage_top}"
        self.run(cmd)

    def make_all_datastores(self, datastore_name="datastore"):
        """
        Create a datastore on each zpool
        """
        pool_data = self.get_pools()
        if pool_data:
            pools = [item[0]
                     for item in pool_data if f"jbod{self.jbod}" in item[0]]
        else:
            sys.exit("No pools found")

        for pool in pools:
            self.create_datastore(pool, datastore_name)

    def mount_all_datastores(self, datastore_name="datastore"):
        """
        This does not work with mutiple deployments
        if there are other datastores it doesn't know what to do
        """
        # Default to "datastore" as the name
        datastores_data = self.get_datastores()
        datastores_data = [item[0] for item in datastores_data]
        datastores = []
        for datastore in datastores_data:
            name = datastore.split("/")[-1]
            if name == datastore_name:
                datastores.append(datastore)
        caps = range(int(self.working_repo.data.distribution.caps))
        for datastore, cap in zip(datastores, caps):
            pbc_path = "/".join([
                f"{self.working_repo.data.storage_top}",
                f"{self.working_repo.name}",
                f"pod{self.pod_num}",
                f"block{self.block_num}",
                f"cap{cap}"
            ])
            self.mount_datastore(
                datastore,
                pbc_path
            )

    def unmount_all_datastores(self):
        """
        TODO needs testing
        """
        datastores_data = self.get_datastores()
        datastores = [item[0] for item in datastores_data]
        for datastore in datastores:
            self.unmount_datastore(datastore)

    def check_zfs_ready(self):
        """
        TODO test this
        Perform some checks to see if ZFS is working and ready for setup
        """
        # Check if storage-start service succeeded
        self.run("systemctl status storage-start")
        output = self.last_command.stdout.decode("utf-8")
        if "SUCCESS" not in output:
            print(output, "storage-start service did not succeed")
            return False
        # check is zfs kernel module is loaded
        self.run("lsmod")
        output = self.last_command.stdout.decode("utf-8")
        if "zfs" not in output:
            print("ZFS kernel module not loaded")
            return False

        # Can we run zfs commands?
        self.run("zfs list")
        if self.last_command.returncode != 0:
            print("can't run zfs list")
            print(self.last_command.stderr.decode("utf-8"))
            return False

        return True

    def setup_zfs(
        self, repo_name, datastore_name="datastore", force_zpools=False
    ):
        # not sure if I need the inputs and to set working repo here
        self.set_working_repo(repo_name)
        self.make_pools(force_zpools)
        self.make_zfs_nfs()

    def deploy_repo(self, repo_name, datastore_name="datastore"):
        """
        ZFSTOOL
        """
        # TODO should check if ZFS is ready and working
        # This probably needs some error checking
        # need to make certain we don't over ride an
        # existing deployment
        if not self.check_zfs_ready:
            # do something
            pass
        self.set_working_repo(repo_name)
        # self.make_pools()
        # self.make_zfs_nfs()
        self.make_all_datastores(datastore_name)
        self.mount_all_datastores(datastore_name)
        self.create_pod_block_cap_scatter()
