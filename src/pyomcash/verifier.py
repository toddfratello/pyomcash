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
from pyomcore.utils import *
from pyomcore.verifier import Verifier, check_blockchain_dir
from .utils import *


class CashVerifier(Verifier):
    def __init__(self, rootdir, gpg_ctx):
        super().__init__(rootdir, gpg_ctx)
        self.balance_sheet = {}
        # viral signing policy: the set of authors can never shrink
        self.author_fprs = set()

    def verify_block(self, idx):
        super().verify_block(idx)
        block = load_block(self.rootdir, idx)
        for action in block['actions']:
            t = action['type']
            if (t == 'register_transaction' or t == 'confirm_transaction' or
                t == 'cancel_transaction' or t == 'annul_transaction' or
                    t == 'reinstate_transaction'):
                transaction_hash = action['transaction']['SHA-512']
                transaction_status = self.transactions[transaction_hash]
                self.process_transaction(t, transaction_status.transaction)

    def process_transaction(self, t, transaction):
        num_participants = len(transaction['participants'])
        fprs = list(map(lambda p: p['gpg'], transaction['participants']))
        for contract in transaction['contracts']:
            if contract['uuid_hash']['SHA-512'] == pyomcash_uuid_hash:
                # Check viral signing policy
                authors = set(
                    map(lambda author: author['gpg'], contract['authors']))
                if not self.author_fprs.issubset(authors):
                    raise Exception('missing authors: ' +
                                    str(self.author_fprs.difference(authors)))
                self.author_fprs = authors
                trade_matrix = contract['trade_matrix']
                check_trade_matrix(num_participants, trade_matrix)
                self.update_balance_sheet(t, fprs, trade_matrix)

    def update_balance_sheet(self, t, fprs, trade_matrix):
        i = fprs.index(self.fpr)
        if t == 'register_transaction':
            for fpr, values in trade_matrix.items():
                value = values[i]
                # register_transaction only allows you to spend money. You don't receive
                # until the transaction is confirmed.
                if value < 0:
                    current_balance = self.balance_sheet.get(fpr, 0)
                    # You can only print your own currency
                    if fpr != self.fpr and current_balance + value < 0:
                        raise Exception(
                            f'Current balance of {fpr} is {current_balance}, so you cannot spend {-value}.')
                    self.balance_sheet[fpr] = current_balance + value
        elif t == 'confirm_transaction':
            for fpr, values in trade_matrix.items():
                value = values[i]
                # Spending already happened in register_transaction. Only need to receive here.
                if value >= 0:
                    current_balance = self.balance_sheet.get(fpr, 0)
                    self.balance_sheet[fpr] = current_balance + value
        elif t == 'cancel_transaction':
            for fpr, values in trade_matrix.items():
                value = values[i]
                # Undo the spending that happened in register_transaction
                if value < 0:
                    current_balance = self.balance_sheet.get(fpr, 0)
                    self.balance_sheet[fpr] = current_balance - value
        elif t == 'annul_transaction':
            for fpr, values in trade_matrix.items():
                value = values[i]
                # Undo the receiving that happened in confirm_transaction
                if value >= 0:
                    current_balance = self.balance_sheet.get(fpr, 0)
                    self.balance_sheet[fpr] = current_balance - value
        elif t == 'reinstate_transaction':
            for fpr, values in trade_matrix.items():
                value = values[i]
                # Undo the effect of annul_transaction
                if value >= 0:
                    current_balance = self.balance_sheet.get(fpr, 0)
                    self.balance_sheet[fpr] = current_balance + value
        else:
            raise Exception('unknown action: ' + t)

    def print_balance_sheet(self):
        for fpr, value in self.balance_sheet.items():
            comment = 'self' if fpr == self.fpr else 'other'
            yield f'{fpr},{value},{comment}\n'

def verify_chain(rootdir):
    numblocks = check_blockchain_dir(rootdir)
    if numblocks == 0:
        raise Exception('no blocks found')
    gpg_ctx = init_local_gpg(rootdir.joinpath(gnupg_dirname))
    v = CashVerifier(rootdir, gpg_ctx)
    for idx in range(0, numblocks):
        try:
            v.verify_block(idx)
        except Exception as e:
            print(f'Error in block {idx}:', e, file=sys.stderr)
            raise Exception(f'Blockchain verification failed in block {idx}')
    return v


if __name__ == "__main__":
    v = verify_chain(pathlib.Path.cwd())
    print(''.join(v.print_balance_sheet()))
