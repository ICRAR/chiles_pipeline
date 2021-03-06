#
#    (c) UWA, The University of Western Australia
#    M468/35 Stirling Hwy
#    Perth WA 6009
#    Australia
#
#    Copyright by UWA, 2012-2015
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
"""
Get the snapshot ids and dates
"""
import logging

from s3_helper import S3Helper
from settings_file import CHILES_BUCKET_NAME


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def main():
    s3_helper = S3Helper()
    bucket = s3_helper.get_bucket(CHILES_BUCKET_NAME)
    cvel_data = set()
    for key in bucket.list(prefix='CVEL/'):
        LOG.info('Checking {0}'.format(key.key))
        elements = key.key.split('/')
        cvel_data.add(elements[1])

    output = '\n'
    for key in sorted(cvel_data):
        output += '{0} '.format(key)
    output += '\n'
    LOG.info(output)

if __name__ == "__main__":
    main()
