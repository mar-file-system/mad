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
import copy
from multiprocessing import Pool
from lxml import etree
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MadBin(object):
    def __init__(self):
        self.bin = os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))) + "/bin"
        self.deploy = self.bin + "/mad-deploy"
        self.mad = self.bin + "/mad"
        self.marfs_init = shutil.which("marfs-init")
        self.fuse = shutil.which("marfs_fuse")


class ConfigTools(object):
    """
    Config manipulation tools
    Important note: You can't pickle an etree element.
    So the tree must be created when needed or you can't
    use multiprocessing.
    """
    def __init__(self, marfs_config):
        self.bin = MadBin()
        self.marfs_config = os.path.abspath(marfs_config)
        

    def new_ns(
        self,
        repo_name,
        ns_name,
        iperms,
        bperms,
        data_quota,
        numfiles,
        nodeploy=False
    ):
        data = self.get_tree(self.marfs_config)
        self.check_exists(data, repo_name)
        try:
            self.check_exists(data, repo_name, ns_name)
            fail = True
        except SystemExit:
            fail = False
        if fail:
            sys.exit(f"Namespace {ns_name} already exists")

        self.sanity_check_perms(bperms)
        self.sanity_check_perms(iperms)
        data_quota = self.quota_bytes(data_quota)
        for repo in data.iter("repo"):
            if repo.attrib["name"] == repo_name:
                md = repo.find("metadata")
                ns = etree.SubElement(md, "ns", name=ns_name)
                quota = etree.SubElement(ns, "quota")
                etree.SubElement(quota, "files").text = numfiles
                etree.SubElement(quota, "data").text = data_quota
                perms = etree.SubElement(ns, "perms")
                etree.SubElement(perms, "interactive").text = iperms
                etree.SubElement(perms, "batch").text = bperms

        self.write_xml(data)
        if not nodeploy:
            self.deploy_ns_gpfs_remote(
                repo_name,
                [ns_name]
            )

    def update_ns(
        self,
        repo_name,
        ns_name,
        new_name,
        iperms,
        bperms,
        data_quota,
        numfiles
    ):
        data = self.get_tree(self.marfs_config)
        self.check_exists(data, repo_name, ns_name)

        for repo in data.iter("repo"):
            if repo.attrib["name"] == repo_name:
                md = repo.find("metadata")
                for ns in md.iter("ns"):
                    if ns.attrib["name"] == ns_name:
                        if new_name:
                            ns.attrib["name"] = new_name
                        q = ns.find("quota")
                        p = ns.find("perms")
                        if numfiles:
                            q.find("files").text = numfiles
                        if data_quota:
                            data_quota = self.quota_bytes(data_quota)
                            q.find("data").text = data_quota
                        if iperms:
                            self.sanity_check_perms(iperms)
                            p.find("interactive").text = iperms
                        if bperms:
                            self.sanity_check_perms(bperms)
                            p.find("batch").text = bperms

        self.write_xml(data)
        # Will need to restart fuse?

    def delete_namespace(
        self,
        repo_name,
        ns_name,
        force=False
    ):
        data = self.get_tree(self.marfs_config)
        self.check_exists(data, repo_name, ns_name)
        confirmed = False
        removed = False
        if force:
            confirmed = True
        else:
            i = input(f"Confirm delete {ns_name}?\n(y/n):")
            if i.lower() == "y":
                confirmed = True

        if confirmed:
            for repo in data.iter("repo"):
                if repo.attrib["name"] == repo_name:
                    md = repo.find("metadata")
                    for ns in md.iter("ns"):
                        if ns.attrib["name"] == ns_name:
                            md.remove(ns)
                            removed = True

        if removed:
            self.write_xml(data)
        else:
            sys.exit(f"Could not remove namespace: {ns_name}")

    def ls(
        self
    ):
        data = self.get_tree(self.marfs_config)
        for repo in data.iter("repo"):
            print("REPO:", repo.attrib["name"])
            for ns in repo.find("metadata").iter("ns"):
                print(" " * 7, ns.attrib["name"])

    def new_repo(
        self,
        repo_name,
        datastore_name,
        jbod,
        pod_block_cap
    ):
        data = self.get_tree(self.marfs_config)
        try:
            self.check_exists(data, repo_name)
            fail = True
        except SystemExit:
            fail = False
        if fail:
            sys.exit(f"Repo {repo_name} already exists")

        r = data.find("repo")
        new_r = copy.deepcopy(r)
        new_r.attrib["name"] = repo_name
        md = new_r.find("metadata")
        for ns in md.iter("ns"):
            md.remove(ns)
        if pod_block_cap:
            new_r.find("data").find("DAL").find(
                "dir_template").text = pod_block_cap
        else:
            dt_t = new_r.find("data").find("DAL").find("dir_template").text
            dt_t = dt_t.replace(r.attrib["name"], new_r.attrib["name"])
            new_r.find("data").find("DAL").find("dir_template").text = dt_t

        data.append(new_r)
        self.write_xml(data)
        self.deploy_repo_remote(
            repo_name,
            datastore_name,
            jbod
        )

    def deploy_repo_remote(
        self,
        repo_name,
        datastore_name,
        jbod
    ):
        self.deploy_zfs_remote(
            repo_name,
            datastore_name,
            jbod
        )
        cfg = MarFSConfig(self.marfs_config)
        c = f"{self.bin.deploy} gpfs {self.marfs_config} {repo_name}"
        hostname = cfg.hosts.metadata_nodes[0].hostname
        self.run_remote(hostname, c)

    def deploy_zfs_remote(self, repo_name, datastore_name, jbod):
        cfg = MarFSConfig(self.marfs_config)
        c = " ".join([
            f"{self.bin.deploy} zfs {self.marfs_config} {repo_name}",
            f"{datastore_name} --jbod {jbod}"
        ])
        items = [[host.hostname, c] for host in cfg.hosts.storage_nodes]
        with Pool(processes=12) as pool:
            pool.starmap(self.run_remote, items)

    def deploy_ns_gpfs_remote(self, repo_name, ns_names):
        cfg = MarFSConfig(self.marfs_config)
        hostname = cfg.hosts.metadata_nodes[0].hostname
        items = []
        for ns_name in ns_names:
            c = f"{self.bin.deploy} ns {self.marfs_config} {repo_name} {ns_name}"
            items.append([hostname, c])
        with Pool(processes=12) as pool:
            pool.starmap(self.run_remote, items)

    def fuse_restart(self):
        # TODO test this
        # TODO consider other options
        cfg = MarFSConfig(self.marfs_config)
        hosts = cfg.hosts.batch_nodes + cfg.hosts.interactive_nodes
        c = f"{self.bin.marfs_init} fuse-restart"
        items = [[host.hostname, c] for host in hosts]
        with Pool(processes=12) as pool:
            pool.starmap(self.run_remote, items)

    def check_exists(self, data, repo_name, ns_name=None):
        repofound = False
        nsfound = False
        for repo in data.iter("repo"):
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
            print(p.stdout.decode("utf-8"))
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

        return tree.getroot()

    def write_xml(self, tree):
        with open(self.marfs_config, "w") as fp:
            fp.write(etree.tostring(tree, pretty_print=True,
                                    xml_declaration=True,
                                    encoding="utf-8").decode("utf-8"))
