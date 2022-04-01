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

import csv
import gpg
import pathlib
import sys
from datetime import timedelta
from pyomcore.verifier import verify_chain
from .utils import create_trade

# For simple trades, where two PYOMers want to trade their own currencies, use
# propose_simple_trade.py. This script is for more complex trades. The trades need
# to be supplied as a CSV file:
#
# ,user0/pyom/,user1/pyom/,user2/pyom/,user3/pyom/
# 96184222620D63E9F0EE9D092A5D1800F9270BD8,-3,1,1,1
# 34494EA12F87A474B5028BC9D1C968A30BB32446,2,-6,2,2
# 5DDC3FDE29D8C7763E076FE3DA5FBBE24247EC55,3,3,-9,3
# 2B92F7405A555697A0F401CCCAC5100A0CB0FEC7,4,4,4,-12
#
# The first row is a list of pyom directories, with the current user in column 1.
# Then there's one row for each currency, with the gpg fingerprint of the currency
# in column 0 and a value for each user in the other columns. The values in each
# row should sum to zero.
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('usage: propose_trade <expiry days> trade_matrix.csv', file=sys.stderr)
        sys.exit(1)
    expiry_delta = timedelta(int(sys.argv[1]))
    reader = csv.reader(open(sys.argv[2], mode='r'), skipinitialspace=True)
    firstrow = next(reader)
    n = len(firstrow)
    if n < 2:
        raise Exception('csv file should have at least 2 columns')
    if firstrow[0] != '':
        raise Exception('first cell of first row should be empty')
    rootdirs = list(map(lambda p: pathlib.Path(p).resolve(), firstrow[1:]))
    trade_matrix = {}
    for row in reader:
        if len(row) != n:
            raise Exception(
                f'row is length {len(row)} but expected {n}: {row}')
        trade_matrix[row[0]] = list(map(lambda x: int(x), row[1:]))
    protoblocks = create_trade(expiry_delta, rootdirs, trade_matrix)
    # Register the transaction in the rootdir from the first column. Can't do
    # it for the other columens because those PYOMers need to do it themselves.
    v = verify_chain(rootdirs[0])
    v.append_block(gpg.Context(), protoblocks[0])
