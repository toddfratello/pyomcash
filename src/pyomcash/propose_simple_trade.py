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

import gpg
import pathlib
import sys
from datetime import timedelta
from pyomcore.verifier import verify_chain
from .utils import create_trade

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('usage: propose_simple_trade path/to/other_pyom_repo <number> <number>', file=sys.stderr)
        sys.exit(1)
    this_rootdir = pathlib.Path.cwd()
    that_rootdir = pathlib.Path(sys.argv[1]).resolve()
    n = int(sys.argv[2])
    m = int(sys.argv[3])
    this_v = verify_chain(this_rootdir)
    that_v = verify_chain(that_rootdir)
    protoblocks = create_trade(
        timedelta(days=7),  # expires in 7 days
        [this_rootdir, that_rootdir],
        {
            this_v.fpr: [-n, n],
            that_v.fpr: [m, -m]
        }
    )
    # Register the transaction in this_rootdir. Can't do it in that_rootdir because
    # the other PYOM needs to do it themselves.
    this_v.append_block(gpg.Context(), protoblocks[0])
