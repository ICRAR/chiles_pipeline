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
Copy the final products to S3
"""
import argparse
import fnmatch
import logging
import os
from os.path import join
from s3_helper import S3Helper

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)-15s:' + logging.BASIC_FORMAT)


def copy_files(args):
    s3_helper = S3Helper(args.aws_access_key_id, args.aws_secret_access_key)
    # Look in the output directory
    for root, dir_names, filenames in os.walk(args.product_dir):
        LOG.debug('root: {0}, dir_names: {1}, filenames: {2}'.format(root, dir_names, filenames))
        for match in fnmatch.filter(dir_names, '13B-266*calibrated_deepfield.ms'):
            result_dir = join(root, match)
            LOG.info('Working on: {0}'.format(result_dir))
            LOG.info('Copying to: {0}/{1}/measurement_set.tar'.format(args.bucket, match))

            #s3_helper.add_tar_to_bucket_multipart(
            #    args.bucket,
            #    '{0}/measurement_set.tar'.format(vis_file, date),
            #    result_dir)


def main():
    parser = argparse.ArgumentParser('Move the final products to S3')
    parser.add_argument('product_dir', help='where the date is stored')
    parser.add_argument('bucket', help='the bucket to use')
    parser.add_argument('aws_access_key_id', help='the AWS access key')
    parser.add_argument('aws_secret_access_key', help='the AWS secret access key')
    args = parser.parse_args()

    copy_files(args)


if __name__ == "__main__":
    main()
