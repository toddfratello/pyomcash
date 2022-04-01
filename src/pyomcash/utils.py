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

import pathlib
from pyomcore.verifier import verify_chain
from pyomcore.utils import *

default_contract_subdir = smart_contracts_dirname.joinpath('pyomcash')

# SHA-512 hash of pyom_smart_contract_uuid.txt
pyomcash_uuid_hash = "0e66b143f19847febbdb3ed6641f183900093c02f18d48924ef515f5bb2c84994c0042b079a728d79111bf55e0932e8ea92ef5eecca11ce8dec10ce40e83f1b9"


def init_participant(rootdir):
    return {
        'rootdir': rootdir,
        'locations_init': [create_pathref(0, pathlib.Path('.'))],
        'protoblock_init': {}
    }

# Get the fpr of the author of this smart contract. Not hardcoded to make testing easier.


def get_author_fpr(rootdir):
    v = verify_chain(rootdir)
    contract_dir = rootdir.joinpath(default_contract_subdir)
    author_keypath = contract_dir.joinpath(smartcontract_pubkey_filename)
    return import_key(v.gpg_ctx, author_keypath.read_bytes())

# Check that the trade_matrix is zero-sum.


def check_trade_matrix(num_participants, trade_matrix):
    for fpr, values in trade_matrix.items():
        if len(values) != num_participants:
            raise Exception(f'Row is not length {n}: {values}')
        total = 0
        for value in values:
            if not isinstance(value, int):
                raise Exception(f'value is not an int: {value}')
            total += value
        if total != 0:
            raise Exception(f'Non-zero sum: sum({values}) == {sum(values)}')


def create_trade(expiry_delta, rootdirs, trade_matrix):
    num_participants = len(rootdirs)
    check_trade_matrix(num_participants, trade_matrix)
    author_fpr = get_author_fpr(rootdirs[0])
    transaction_init = {
        'numlocations': 1,
        'contracts': [
            {
                'path': create_pathref(0, default_contract_subdir),
                'uuid_hash': {'SHA-512': pyomcash_uuid_hash},
                'authors': [{'gpg': author_fpr}],
                'trade_matrix': trade_matrix
            }
        ]
    }
    participants = list(map(init_participant, rootdirs))
    return create_transaction(participants, expiry_delta, transaction_init)
