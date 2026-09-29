import json
import requests
import os
import sys
import csv
import subprocess
import getpass
import pathlib

import argparse
import time
from typing import NamedTuple
from datetime import timedelta



class Args(NamedTuple):
    """ Command-line arguments """
    url: str
    deploy: str
    db_name: str


def get_args() -> Args:

    """ Get command-line arguments """

    parser = argparse.ArgumentParser(
        description='Script for generating backups',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)


    parser.add_argument('url',
                        metavar='url',
                        help='url of the service')

    parser.add_argument('deploy',
                        metavar='deploy',
                        help='name of the deploy')
    
    parser.add_argument('db_name',
                        metavar='db_name',
                        help='name of the db to generate backup')
                        
    args = parser.parse_args()


    return Args(args.url, args.deploy, args.db_name)


def get_list_db(url):
    action_url = "http://{}/web/database/list".format(url)
    data = {"params": {}}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(action_url, data=json.dumps(data), headers=headers)
        db = response.json()
    except Exception as e:
        print("URL:", url)
        print("Connection establishment failed!")
        print(e)
        print("------------------------------")
        db = {"error": e}

    return db


def dump_db_odoo(db_name):

    try:
        operation = subprocess.check_output('sh odoo-backup.sh {}'.format(db_name),shell=True).decode('utf-8')
        print('Backup files generated!')

        output_from_script = operation.splitlines()
        dump_name = output_from_script[-1]

    except Exception as e:
        dump_name = False
        print("Error generating backup files: ")
        print(e)

    return dump_name



def upload_dump_to_s3(list_db, data):
    db_name = data['db_name']
    directory = data['directory']
    for db in list_db:
        if db == db_name:
            print('DATABASE:', db)
            dump_name = dump_db_odoo(db)
            if dump_name:
                bucket_name = 's3://tools-ganemo/{}'.format(dump_name)
                dir_dump = '{}{}'.format(directory, dump_name)
                operation = 'aws s3 cp {} {} --no-progress --only-show-errors'.format(dir_dump, bucket_name)
                print('Uploading...')
                os.system(operation)
                print('Bucket:', bucket_name)
                os.system('rm {}*'.format(directory))
                print("Link to download db: ", db)
                print("https://tools-ganemo.s3.amazonaws.com/{}".format(dump_name))
            print('-------------------------------------')
        else:
            print('Will not generate backup of DATABASE:', db)
       
            
        



def generate_backups(url, deploy, db_name):

    current_user = getpass.getuser()
    file_route = "/home/{0}/backup/".format(current_user)

    if not pathlib.Path(file_route).exists():
        os.system("mkdir /home/{0}/backup/".format(current_user))

    data = {
        'deploy': deploy,
        'directory': '/home/{0}/backup/'.format(current_user),
        'db_name': db_name
    }

    db = get_list_db(url)
    if db.get('error'):
        print('¡CONNECTION PROBLEM!\n Review data and try again.')
    else:
        list_db = db['result']
        print('DEPLOY:', data['deploy'])
        upload_dump_to_s3(list_db, data)



def main():

    args = get_args()
    url, deploy, db_name = args.url, args.deploy, args.db_name


    try:

        generate_backups(url,deploy,db_name)

    except Exception as e:
        print("Error: ")
        print(e)
        print('-------------------------------------')


if __name__ == '__main__':
    main()
