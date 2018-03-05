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
import re
import datetime
import os

ec = boto3.client('ec2')
iam = boto3.client('iam')

"""
This function looks at *all* snapshots that have a "DeleteOn" tag containing
the current day formatted as YYYY-MM-DD. This function should be run at least
daily.
"""

if 'BACKUP_CREATION_TAG' in os.environ:
    tag = os.environ['BACKUP_CREATION_TAG']
else:
    tag = 'Backup'

if 'BACKUP_RETENTION_TAG' in os.environ:
    ret_period = os.environ['BACKUP_RETENTION_TAG']
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
    account_ids = list()
    try:
        """
        You can replace this try/except by filling in `account_ids` yourself.
        Get your account ID with:
        > import boto3
        > iam = boto3.client('iam')
        > print iam.get_user()['User']['Arn'].split(':')[4]
        """
        iam.get_user()
    except Exception as e:
        # use the exception message to get the account ID the function executes under
        account_ids.append(re.search(r'(arn:aws:sts::)([0-9]+)', str(e)).groups()[1])


    # calculate time
    delete_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=retention)
    print "Configured retension %s" % delete_time

    # get all instaces with selected tag
    filters = [
        {'Name': 'tag-key', 'Values': ['BackupTag']},
        {'Name': 'tag-value', 'Values': [tag]},
    ]
    snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters)


    for snap in snapshot_response['Snapshots']:
        delete_on = [i for i in snap['Tags'] if i['Key'] == 'DeleteOn'][0]['Value']
        print "Checking snapshot %s with retension %s" % (snap['SnapshotId'], delete_on)
        # if delete time is more then create time, drop the snapshot
        if datetime.datetime.strptime(delete_on, '%Y-%m-%d-%H-%M') < delete_time:
            print "Deleting snapshot %s" % snap['SnapshotId']
            ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
