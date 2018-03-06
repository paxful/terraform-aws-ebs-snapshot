# Copyright 2015 Ryan S Brown
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import boto3
import collections
import datetime
import os

ec = boto3.client('ec2')

if 'BACKUP_TAG' in os.environ:
    tag = os.environ['BACKUP_TAG']
else:
    tag = 'Backup'

if 'BACKUP_RETENTION' in os.environ:
    ret_period = os.environ['BACKUP_RETENTION']
else:
    ret_period = '7'

# calculate retention in minutes
if 'd' in ret_period:
    retention = 24 * 60 * ret_period.split('d')[0]
elif 'h' in ret_period:
    retention = 60 * ret_period.split('h')[0]
else:
    retention = int(ret_period)

def lambda_handler(event, context):
    reservations = ec.describe_instances(
        Filters=[
            {'Name': 'tag:%s' % tag, 'Values': ['true', 'yes', '1']},
        ]
    ).get(
        'Reservations', []
    )

    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])

    print "Found %d instances with tag %s that need backing up" % (len(instances), tag)

    for instance in instances:
        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            vol_id = dev['Ebs']['VolumeId']
            try:
                instance_name = [i for i in instance['Tags'] if i['Key'] == 'Name'][0]['Value']
            except IndexError:
                instance_name = instance['InstanceId']

            print "Found EBS volume %s on instance %s (%s)" % (
                vol_id, instance['InstanceId'], instance_name)

            snap = ec.create_snapshot(
                VolumeId=vol_id,
            )

            delete_date = datetime.datetime.utcnow() + datetime.timedelta(minutes=retention)
            delete_fmt = delete_date.strftime('%Y-%m-%d-%H-%M')

            print "Retaining snapshot %s of volume %s from instance %s at %s" % (
                snap['SnapshotId'],
                vol_id,
                instance['InstanceId'],
                delete_fmt,
            )

            ec.create_tags(
                Resources=[snap['SnapshotId']],
                Tags=[
                    {'Key': 'BackupTag', 'Value': tag},
                    {'Key': 'DeleteOn', 'Value': delete_fmt},
                    {'Key': 'Name', 'Value': instance_name},
                ]
            )
