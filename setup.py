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

from setuptools import setup

setup(
    name='pyomcash',
    version='1.0.0',
    author='Todd Fratello',
    author_email='ToddFratello@gmail.com',
    url='https://github.com/toddfratello/pyomcash',
    package_dir={'': 'src'},
    packages=['pyomcash'],
    install_requires=['pyomcore'],
    license='GPLv3',
)
