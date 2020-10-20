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

from src.data_bindings import MarFSConfig
import subprocess
import sys
import os
import shutil
from lxml import etree
from multiprocessing import Pool
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConfigTools(object):
    """
    Config manipulation tools
    """
    def deploy_zfs_remote(self, marfs_config, repo_name, datastore_name, jbod):
        cfg = MarFSConfig(marfs_config)
        MAD = shutil.which("mad")
        c = join([
            f"{MAD} deploy_zfs {marfs_config} {repo_name}",
            f"--datastore {datastore_name} --jbod {jbod}"
        ])
        items = [[host.hostname, c] for host in cfg.hosts.storage_nodes]
        with Pool(processes=6) as pool:
            pool.map(self.run_remote, items)
        
    def deploy_gpfs_remote(self, marfs_config, repo_name, gpfs_device):
        cfg = MarFSConfig(marfs_config)
        MAD = shutil.which("mad")
        c = f"{MAD} deploy_gpfs {marfs_config} {repo_name} {gpfs_device}"
        hostname = cfg.hosts.metadata_nodes[0].hostname
        self.run_remote(hostname, c)

    def check_exists(self, tree, repo_name, ns_name=None):
        repofound = False
        nsfound = False
        for repo in tree.iter("repo"):
            if repo.attrib["name"] == repo_name:
                repofound = True
                if ns_name:
                    for ns in repo.find("metadata").iter("ns"):
                        if ns.attrib["name"] == ns_name:
                            nsfound = True

        if not repofound:
            sys.exit(f"Could not find repo: {repo_name}")

        if ns_name and not nsfound:
            sys.exit(f"Could not find namespace: {ns_name}")

    def run_remote(self, hostname, cmd_str, get_output=True, timeout=30):
        cmd = f"ssh {hostname} {cmd_str}"
        try:
            p = subprocess.run(
                cmd.split(),
                capture_output=get_output,
                timeout=timeout
            )
        except TypeError:
            if get_output:
                p = subprocess.run(
                    cmd.split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=timeout
                )
            else:
                p = subprocess.run(
                    cmd.split(),
                    timeout=timeout
                )

        if len(p.stderr):
            print(p.stderr.decode("utf-8"))

    def quota_bytes(self, data_quota):
        return str(1073741824 * data_quota)

    def sanity_check_perms(self, perms):
        valid_perms = ["RD", "WD", "RM", "WM", "UD", "TD"]
        perms = perms.split(",")
        for p in perms:
            if p not in valid_perms:
                raise ValueError

    def get_tree(self, config_path):
        parser = etree.XMLParser(remove_blank_text=True)
        with open(config_path, "r") as fp:
            tree = etree.parse(fp, parser=parser)

        return tree

    def write_xml(self, tree, config_path):
        with open(config_path, "w") as fp:
            fp.write(etree.tostring(tree, pretty_print=True,
                                    xml_declaration=True,
                                    encoding="utf-8").decode("utf-8"))
