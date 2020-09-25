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

import argparse
import sys
import os
from storage_tools.interfaces import storage as sti
from storage_tools.interfaces import metadata as mdi

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def single_node_example():
    config_file = "./config/single_node.xml"
    repo_name = "single"
    si = sti.StorageInterface(config_file, repo_name)
    si._trick_valid_host()
    si.set_working_repo(repo_name)
    blocks = int(si.working_repo.dal.n) + int(si.working_repo.dal.e)
    for block in range(blocks):
        si.block_num = int(block)
        si.create_pod_block_cap_scatter()

    mi = mdi.MetadataInterface(config_file, repo_name)
    mi.deploy_repo(repo_name)
    # need to link storage caps under metadata caps somehow


def deploy_zfs(args):
    si = sti.ZFSInterface(args.marfs_config, args.repo_name, args.jbod)
    si.deploy_repo(args.repo_name, args.datastore_name)


def deploy_gpfs(args):
    mi = mdi.GPFSInterface(
        args.marfs_config,
        args.repo_name,
        args.gpfs_device
    )
    mi.deploy_repo(args.repo_name)


def setup_zfs(args):
    si = sti.ZFSInterface(args.marfs_config, args.repo_name, args.jbod)
    si.setup_zfs(args.repo_name, args.datastore_name, args.force_zpools)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # deploy_zfs
    parser_deploy_zfs = subparsers.add_parser(
        'deploy_zfs',
        prog="deploy_zfs",
        help="Deploy a MarFS storage cluster to ZFS"
    )
    parser_deploy_zfs.add_argument(
        'marfs_config',
        metavar='MARFSCONFIGRC',
        type=str,
        help='Path to MarFS Configuration File'
    )
    parser_deploy_zfs.add_argument(
        'repo_name',
        metavar='REPOSITORY_NAME',
        type=str,
        help='Repository Name to deploy'
    )
    parser_deploy_zfs.add_argument(
        '--datastore_name',
        type=str,
        metavar="",
        help="Name of datastore to deploy",
        default="datastore"
    )
    parser_deploy_zfs.add_argument(
        '--jbod',
        type=str,
        metavar="",
        help="JBOD number",
        default="1"
    )
    parser_deploy_zfs.set_defaults(func=deploy_zfs)
    # Deploy GPFS
    parser_deploy_gpfs = subparsers.add_parser(
        'deploy_gpfs',
        prog="deploy_gpfs",
        help="Deploy MarFS to GPFS"
    )
    parser_deploy_gpfs.add_argument(
        'marfs_config',
        metavar='MARFSCONFIGRC',
        type=str,
        help='Path to MarFS Configuration File'
    )
    parser_deploy_gpfs.add_argument(
        'repo_name',
        metavar='REPOSITORY_NAME',
        type=str,
        help='Repository Name to deploy'
    )
    parser_deploy_gpfs.add_argument(
        'gpfs_device',
        metavar='GPFS_DEV',
        type=str,
        help='Path to GPFS device'
    )
    parser_deploy_gpfs.set_defaults(func=deploy_gpfs)

    parser_setup_zfs = subparsers.add_parser(
        'setup_zfs',
        prog="setup_zfs",
        help="Setup ZFS zpools for MarFS"
    )
    parser_setup_zfs.add_argument(
        'marfs_config',
        metavar='MARFSCONFIGRC',
        type=str,
        help='Path to MarFS Configuration File'
    )
    parser_setup_zfs.add_argument(
        'repo_name',
        metavar='REPOSITORY_NAME',
        type=str,
        help='Repository Name to deploy'
    )
    parser_setup_zfs.add_argument(
        '--datastore_name',
        type=str,
        metavar="",
        help="Name of datastore to deploy",
        default="datastore"
    )
    parser_setup_zfs.add_argument(
        '--jbod',
        type=str,
        metavar="",
        help="JBOD number",
        default="1"
    )
    parser_setup_zfs.add_argument(
        '--force_zpools',
        type=bool,
        metavar="",
        help="Force zpool creation",
        default=False
    )
    parser_setup_zfs.set_defaults(func=setup_zfs)

    args = parser.parse_args()
    args.func(args)
