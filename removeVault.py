#!/usr/bin/env python

# -*- coding: UTF-8 -*-

import sys
import json
import time
import os.path
import boto.glacier

jobIDfile = '/tmp/glacierRemoveJobID'

# Get arguments
regionName = sys.argv[1]
vaultName = sys.argv[2]

# Load credentials
f = open('credentials.json', 'r')
config = json.loads(f.read())
f.close()

print 'Connect to Amazon Glacier...'

glacier = boto.glacier.connect_to_region(regionName, aws_access_key_id=config['AWSAccessKeyId'], aws_secret_access_key=config['AWSSecretKey'])

print 'Get selected vault...'
vault = glacier.get_vault(vaultName)

if len(sys.argv) == 4:
	print 'Get job ID from args...'
	jobID = sys.argv[3]
elif os.path.isfile(jobIDfile):
	print 'Get job ID from file...'
	f = open(jobIDfile, 'r')
	jobID = f.read()
	f.close()
else:
	print 'Initiate inventory retrieval job...'
	jobID = vault.retrieve_inventory(description='Python Amazon Glacier Removal Tool')

print 'Job ID : '+ jobID

print 'Writing job ID file...'
f = open(jobIDfile, 'w')
f.write(jobID)
f.close()

# Get job status
job = vault.get_job(jobID)

while job.status_code == 'InProgress':
	print 'Inventory not ready, sleep for 30 mins...'

	time.sleep(60*30)

	job = vault.get_job(jobID)

if job.status_code == 'Succeeded':
	print 'Inventory retrieved, parsing data...'
	inventory = json.loads(job.get_output())

	print 'Loop over archives...'
	for archive in inventory['ArchiveList']:
		print 'Remove archive ID : '+ archive['ArchiveId']
		vault.delete_archive(archive['ArchiveId'])

	print 'Removing vault...'
	vault.remove()

	print 'Vault removed.'

else:
	print 'Vault retrieval failed.'