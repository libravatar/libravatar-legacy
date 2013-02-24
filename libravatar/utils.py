# Copyright (C) 2011, 2013  Francois Marier <francois@libravatar.org>
#
# This file is part of Libravatar
#
# Libravatar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Libravatar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Libravatar.  If not, see <http://www.gnu.org/licenses/>.

import logging
from os import unlink, path

import settings  # pylint: disable=W0403


# functions common to all gearman workers

def delete_if_exists(filename):
    if path.isfile(filename):
        unlink(filename)


def is_hex(s):
    return set(s).issubset('0123456789abcdefABCDEF')


def is_hash_pair(element):
    if not isinstance(element, list):
        return False
    if len(element) < 2:
        return False

    return (element[0] is None or is_hex(element[0])) and (element[1] is None or is_hex(element[1]))


def create_logger(worker_name):
    log_filename = settings.GEARMAN_WORKER_LOGFILE
    log_level = logging.INFO

    logger = logging.getLogger(worker_name)
    logger.setLevel(log_level)
    handler = logging.FileHandler(log_filename)
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s: %(name)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
