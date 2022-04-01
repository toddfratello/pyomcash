#!/usr/bin/env python3

# Copyright 2022 Todd Fratello
# This file is part of pyomcash.
#
# pyomcash is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyomcash is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyomcash. If not, see <https://www.gnu.org/licenses/>.

import sys
import pathlib
import time
from datetime import timedelta
from pyomcore.utils import *
from pyomcore.initialize_blockchain import initialize_blockchain
from pyomcore.confirm_transactions import confirm_transactions
from pyomcore.check_dependency_chain import check_dependency_chain
from pyomcore.add_smart_contract import add_smart_contract
from pyomcore.annul_transaction import annul_transaction
from pyomcore.reinstate_transaction import reinstate_transaction
import pyomcore.verifier
from pyomcash.utils import create_trade
import pyomcash.verifier

tmpdir = pathlib.Path(sys.argv[1])
pyomcore_url = sys.argv[2]
pyomcash_url = sys.argv[3]

tmpdir.mkdir(parents=True, exist_ok=True)
tmpdir = tmpdir.resolve()

users = []
gpg_dirs = []
rootdirs = []
fprs = []

# initialize 4 users
for i in range(0, 4):
    name = f'user{i}'
    userdir = tmpdir.joinpath(name)
    userdir.mkdir(parents=True, exist_ok=True)
    # Create a directory to simulate the users ~/.gnupg
    gpg_dir = userdir.joinpath('gnupg')
    gpg_dir.mkdir(parents=True, exist_ok=True)
    gpg_ctx = init_local_gpg(gpg_dir)
    gpg_ctx.create_key(name, algorithm='rsa4096', sign=True, certify=True)
    rootdir = userdir.joinpath('pyom')
    rootdir.joinpath(smart_contracts_dirname).mkdir(
        parents=True, exist_ok=True)
    result = subprocess.run(['git', 'clone', pyomcore_url, rootdir.joinpath(
        smart_contracts_dirname).joinpath('pyomcore').as_posix()], capture_output=True)
    result.check_returncode()
    result = subprocess.run(['git', 'clone', pyomcash_url, rootdir.joinpath(
        smart_contracts_dirname).joinpath('pyomcash').as_posix()], capture_output=True)
    result.check_returncode()
    v = initialize_blockchain(gpg_ctx, rootdir)
    add_smart_contract(
        gpg_ctx, rootdir, smart_contracts_dirname.joinpath('pyomcash'))
    # Add to lists
    users.append(name)
    gpg_dirs.append(gpg_dir)
    rootdirs.append(rootdir)
    fprs.append(v.fpr)
    print(f'created user{i}')

# 4-way trade
trade_matrix4 = {
    fprs[0]: [-3, 1, 1, 1],
    fprs[1]: [2, -6, 2, 2],
    fprs[2]: [3, 3, -9, 3],
    fprs[3]: [4, 4, 4, -12]
}
protoblocks = create_trade(timedelta(days=1), rootdirs, trade_matrix4)
print('create trade')

# Register transaction
for gpg_dir, rootdir, protoblock in zip(gpg_dirs, rootdirs, protoblocks):
    gpg_ctx = gpg.Context()
    gpg_ctx.home_dir = gpg_dir.as_posix()
    idx = most_recent_block_idx(rootdir)
    block = load_block(rootdir, idx)
    fpr = block['owner']['gpg']
    create_block(gpg_ctx, rootdir, idx+1, fpr, protoblock)
    print('register transaction', rootdir.parent.name)

# Confirm transaction
for gpg_dir, this_rootdir in zip(gpg_dirs, rootdirs):
    gpg_ctx = gpg.Context()
    gpg_ctx.home_dir = gpg_dir.as_posix()
    for that_rootdir in rootdirs:
        confirm_transactions(gpg_ctx, this_rootdir,
                             that_rootdir, confirm_only=False)
        print('confirm transaction', this_rootdir.parent.name,
              that_rootdir.parent.name)

check_dependency_chain(rootdirs[0], rootdirs[1:])
print('check_dependency_chain')

# Test annulling a transaction
transaction_hash = protoblocks[0]['actions'][-1]['transaction']['SHA-512']
annul_transaction(gpg.Context(home_dir=gpg_dirs[0].as_posix(
)), rootdirs[0], transaction_hash, "test annul_transaction")
print('annul_transaction')
check_dependency_chain(rootdirs[0], rootdirs[1:])
print('check_dependency_chain')
reinstate_transaction(gpg.Context(
    home_dir=gpg_dirs[0].as_posix()), rootdirs[0], transaction_hash)
print('reinstate_transaction')
check_dependency_chain(rootdirs[0], rootdirs[1:])
print('check_dependency_chain')

# new 4-way trade with very short expiration
protoblocks = create_trade(timedelta(seconds=2), rootdirs, trade_matrix4)
print('create trade')

# Only the first two users register the transaction before the expiry
for gpg_dir, rootdir, protoblock in list(zip(gpg_dirs, rootdirs, protoblocks))[0:2]:
    gpg_ctx = gpg.Context()
    gpg_ctx.home_dir = gpg_dir.as_posix()
    idx = most_recent_block_idx(rootdir)
    block = load_block(rootdir, idx)
    fpr = block['owner']['gpg']
    create_block(gpg_ctx, rootdir, idx+1, fpr, protoblock)
    print('register transaction', rootdir.parent.name)

# Let transaction expire
print('start sleep(3)')
time.sleep(3)
print('stop sleep(3)')

# Add some trivial blocks
for gpg_dir, rootdir in zip(gpg_dirs, rootdirs):
    gpg_ctx = gpg.Context()
    gpg_ctx.home_dir = gpg_dir.as_posix()
    idx = most_recent_block_idx(rootdir)
    block = load_block(rootdir, idx)
    fpr = block['owner']['gpg']
    create_block(gpg_ctx, rootdir, idx+1, fpr, {'actions': []})
    print('create trivial block', rootdir.parent.name)

# Attempt to confirm transaction
for gpg_dir, this_rootdir in zip(gpg_dirs, rootdirs):
    gpg_ctx = gpg.Context()
    gpg_ctx.home_dir = gpg_dir.as_posix()
    for that_rootdir in rootdirs:
        confirm_transactions(gpg_ctx, this_rootdir,
                             that_rootdir, confirm_only=False)
        print('confirm transaction', this_rootdir.parent.name,
              that_rootdir.parent.name)

# Verify
for rootdir in rootdirs:
    pyomcore.verifier.verify_chain(rootdir)
    print('verify', rootdir.parent.name)
    v = pyomcash.verifier.verify_chain(rootdir)
    print(''.join(v.print_balance_sheet()))
