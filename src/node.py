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
import socket
import subprocess
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class NodeBase(object):
    def __init__(self, marfs_config=None, marfs_repo=None):
        """
        Base object for storage interfaces
        The NodeBase holds common methods between all storage and metadata
        nodes this helps keep configuration generic across all nodes
        """
        self.config = MarFSConfig(marfs_config)
        self.fqdn = socket.getfqdn()
        self.plist = []
        self.pod_num = None
        self.block_num = None
        self.last_command = None
        self.valid = self.valid_host()
        self.working_repo = None
        self.set_working_repo(marfs_repo)

    @property
    def hostname(self):
        hostname = self.fqdn.split(".")
        if hostname[0]:
            return hostname[0]
        else:
            return self.fqdn

    def valid_host(self):
        """
        Checks to make certain this host is in the config file
        """
        found = False
        hostnames = [self.fqdn, self.hostname]
        for hostname in hostnames:
            if hostname in self.config.hosts.all_hostnames:
                found = True

        return found

    def set_working_repo(self, repo_name):
        """
        repos cannot be indexed by name easily, so we set a
        "working" repo to address it like a normal object
        """
        self.working_repo = None
        for repo in self.config.repos:
            if repo.name == repo_name:
                self.working_repo = repo

        if not self.working_repo:
            # TODO
            # If we can't match the repo we should stop
            # But perhaps a sys exit is too much?
            # If loaded by another tool we should not die
            # raise an exception we can handle
            # if calling this file we should die
            sys.exit("Repo not found")

    def get_pod_block_caps(self, top):
        """
        Creates a list of path strings underneath top argument
        """
        dirs = []
        for cap in range(int(self.working_repo.data.distribution.caps)):
            pbc_path = "/".join([
                f"{top}",
                f"{self.working_repo.name}",
                f"pod{self.pod_num}",
                f"block{self.block_num}",
                f"cap{cap}"
            ])
            dirs.append(pbc_path)

        return dirs

    def run(self, cmd, get_output=True, timeout=30):
        """
        takes a string and executes the command
        """
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

        self.plist.append(p)
        self.last_command = p
