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
                        
    args = parser.parse_args()


    return Args(args.url, args.deploy)


SQL_BASES = ("SELECT datname FROM pg_database "
             "WHERE datdba = (SELECT usesysid FROM pg_user WHERE usename = current_user) "
             "AND datallowconn AND NOT datistemplate AND datname <> 'postgres' ORDER BY datname")


def get_list_db(url=None):
    """Bases de la instancia: las que son del rol de PostgreSQL del pod, leidas con psql.

    Antes se pedian a Odoo por /web/database/list. Desde el 11-oct-2026 las instancias tienen el gestor de bases web
    apagado (list_db = False: con el encendido, quien tuviera la clave maestra descargaba o borraba bases desde
    internet) y ese endpoint responde AccessDenied: el respaldo se habria quedado sin bases EN SILENCIO. Es la misma
    consulta que usa Odoo para listar (y el entrypoint de la imagen); las variables son las que ya exige odoo-backup.sh.
    `url` se ignora: queda por compatibilidad con los jobs que llaman `<script> localhost:8069 ...`.
    """
    env = dict(os.environ, PGPASSWORD=os.environ.get('DB_ENV_POSTGRES_PASSWORD', ''), PGCONNECT_TIMEOUT='10', LC_ALL='C')
    cmd = ['psql', '-w', '-qAt', '-h', os.environ.get('DB_PORT_5432_TCP_ADDR', ''),
           '-p', os.environ.get('DB_PORT_5432_TCP_PORT', '5432'), '-U', os.environ.get('DB_ENV_POSTGRES_USER', ''),
           '-d', 'postgres', '-c', SQL_BASES]
    try:
        r = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                           timeout=60)
    except Exception as e:
        return {"error": e}
    if r.returncode != 0:
        return {"error": (r.stderr or '').strip()[-300:] or 'psql rc=%s' % r.returncode}
    return {"result": [l.strip() for l in r.stdout.splitlines() if l.strip()]}


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
    deploy = data['deploy']
    directory = data['directory']
    for db in list_db:
        print('DATABASE:', db)
        if 'test' in db:
            print('Test database will not be downloaded!!!')
            continue
        else:
            dump_name = dump_db_odoo(db)
            if dump_name:
                bucket_name = 's3://backups-odoo-prod/{}/{}/{}'.format(deploy, db, dump_name)
                dir_dump = '{}{}'.format(directory, dump_name)
                operation = 'aws s3 cp {} {} --no-progress --only-show-errors'.format(dir_dump, bucket_name)
                print('Uploading...')
                os.system(operation)
                print('Bucket:', bucket_name)
                os.system('rm {}*'.format(directory))
        print('-------------------------------------')



def generate_backups(url, deploy):

    current_user = getpass.getuser()
    file_route = "/home/{0}/backup/".format(current_user)

    if not pathlib.Path(file_route).exists():
        os.system("mkdir /home/{0}/backup/".format(current_user))

    data = {
        'deploy': deploy,
        'directory': '/home/{0}/backup/'.format(current_user)
    }

    db = get_list_db(url)
    if db.get('error'):
        print('¡CONNECTION PROBLEM!\n Review data and try again.')
        print('ERROR al listar las bases: %s' % db.get('error'))
        sys.exit(1)
    else:
        list_db = db['result']
        print('DEPLOY:', data['deploy'])
        upload_dump_to_s3(list_db, data)



def main():

    args = get_args()
    url, deploy = args.url, args.deploy


    try:

        generate_backups(url,deploy)

    except Exception as e:
        print("Error: ")
        print(e)
        print('-------------------------------------')


if __name__ == '__main__':
    main()
