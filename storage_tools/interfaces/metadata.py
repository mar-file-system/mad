# Copyright(c) 2015, Los Alamos National Security, LLC
# All rights reserved.

# Copyright 2015.  Los Alamos National Security, LLC. This software was produced
# under U.S. Government contract DE-AC52-06NA25396 for Los Alamos National
# Laboratory(LANL), which is operated by Los Alamos National Security, LLC for
# the U.S. Department of Energy. The U.S. Government has rights to use, reproduce,
# and distribute this software.  NEITHER THE GOVERNMENT NOR LOS ALAMOS NATIONAL
# SECURITY, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR ASSUMES ANY LIABILITY
# FOR THE USE OF THIS SOFTWARE.  If software is modified to produce derivative
# works, such modified software should be clearly marked, so as not to confuse it
# with the version available from LANL.

# Additionally, redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of Los Alamos National Security, LLC, Los Alamos National
# Laboratory, LANL, the U.S. Government, nor the names of its contributors may be
# used to endorse or promote products derived from this software without specific
# prior written permission.

# THIS SOFTWARE IS PROVIDED BY LOS ALAMOS NATIONAL SECURITY, LLC AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL LOS ALAMOS NATIONAL SECURITY, LLC OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#                          SUBSTITUTE GOODS OR SERVICES
#                          LOSS OF USE, DATA, OR PROFITS
#                          OR BUSINESS
#                          INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# -----
# NOTE:
# -----
# MarFS is released under the BSD license.

# MarFS was reviewed and released by LANL under Los Alamos Computer Code identifier:
# LA-CC-15-039.

# MarFS uses libaws4c for Amazon S3 object communication. The original version
# is at https: // aws.amazon.com/code/Amazon-S3/2601 and under the LGPL license.
# LANL added functionality to the original work. The original work plus
# LANL contributions is found at https: // github.com/jti-lanl/aws4c.

# GNU licenses can be found at http: // www.gnu.org/licenses/.

from storage_tools.node import NodeBase
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MetadataInterface(NodeBase):
    def __init__(self, marfs_config=None, marfs_repo=None):
        super().__init__(marfs_config, marfs_repo)

    def create_pod_block_caps(self):
        # Metadata nodes can create all pod/block/cap dirs from one node
        # For both GPFS and single node deployments
        for pod in range(int(self.working_repo.dal.pods)):
            self.pod_num = pod
            for block in range(int(self.working_repo.dal.blocks)):
                self.block_num = block
                caps = self.get_pod_block_caps(self.config.mdfs_top)
                for cap in caps:
                    os.makedirs(cap, exist_ok=True)

    def deploy_namespace(self, namespace):
        """
        """
        link_target = self.config.mdfs_top + "/" + namespace.name
        md_path = link_target + "/mdfs"
        trash_target = link_target + "/trash"
        fsinfo_path = link_target + "/fsinfo"
        os.makedirs(md_path, exist_ok=True)
        os.makedirs(trash_target, exist_ok=True)
        with open(fsinfo_path, "w") as fp:
            pass
        

    def deploy_repo(self, repo_name):
        self.set_working_repo(repo_name)
        self.create_pod_block_caps()
        for ns in self.working_repo.namespaces:
            self.deploy_namespace(ns)
        

class GPFSInterface(MetadataInterface):
    def __init__(self, marfs_config=None, marfs_repo=None, gpfs_device=None):
        self.gpfs_dev = gpfs_device
        print(marfs_repo)
        super().__init__(marfs_config, marfs_repo)

    def list_all_filesets(self):
        self.run(f"mmlsfileset {self.gpfs_dev}")
    
    def list_fileset(self, target):
        self.run(f"mmlsfileset {self.gpfs_dev} -J {target}")

    def create_fileset(self, name):
        self.run(f"mmcrfileset {self.gpfs_dev} {name}")

    def link_fileset(self, name, target):
        if not os.path.isdir(target):
            self.run(f"mmlinkfileset {self.gpfs_dev} {name} -J {target}")

    def check_mdfs_top(self):
        try:
            contents = os.listdir(self.config.mdfs_top)
            if len(contents) == 0:
                print("md top is empty")
                #return False
        except FileNotFoundError:
            print("md top not found")
            return False

        return True

    def deploy_repo(self, repo_name):
        self.set_working_repo(repo_name)
        # TODO might need error checking to make sure MDFS top is ready
        self.create_pod_block_caps()
        # Now we can deploy the whole repo and pass on existing namespaces
        for ns in self.working_repo.namespaces:
            try:
                self.deploy_namespace(ns)
            except FileExistsError:
                print("doing nothing")


    def deploy_namespace(self, namespace):
        link_target = self.config.mdfs_top + "/" + namespace.name
        md_path = link_target + "/" + "mdfs"
        trash_target = link_target + "/trash"
        fsinfo_path = link_target + "/fsinfo"
        if os.path.isdir(link_target): 
            print("ERROR: NAMESPACE LINK TARGET EXISTS ALREADY")
            raise FileExistsError
        if os.path.isdir(md_path):
            print("ERROR: METADATA PATH EXISTS ALREADY")
            raise FileExistsError
        if os.path.isdir(trash_target):
            print("ERROR: NAMESPACE TRASH MAY EXIST ALREADY")
            raise FileExistsError
        if os.path.isfile(fsinfo_path):
            print("ERROR: FSINFO ALREADY EXISTS")
            raise FileExistsError
        
        self.create_fileset(namespace.name)
        self.link_fileset(namespace.name, link_target)
        os.mkdir(md_path)
        self.create_fileset(namespace.name + "-trash")
        self.link_fileset(namespace.name + "-trash", trash_target)
        with open(fsinfo_path, "w") as fp:
            pass
