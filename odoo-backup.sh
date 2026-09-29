#!/bin/bash


### Enviroment Variables needed to run the odoo-backup script ###
### that most of them are found in the .env file of the project ###
if [ -z "$DB_ENV_POSTGRES_USER" ]; then
    echo "ERROR: Instalation error, DB_ENV_POSTGRES_USER is not defined"
    exit 1
fi
if [ -z "$HOME" ]; then
    echo "ERROR: Instalation error, HOME is not defined"
    exit 1
fi
if [ -z "$DB_PORT_5432_TCP_ADDR" ]; then
    echo "ERROR: Instalation error, DB_PORT_5432_TCP_ADDR is not defined"
    exit 1
fi
if [ -z "$ODOO_DATA_DIR" ]; then
    echo "ERROR: Instalation error, ODOO_DATA_DIR is not defined"
    exit 1
fi

if [ -z "$DB_ENV_POSTGRES_PASSWORD" ]; then
    echo "ERROR: Instalation error, DB_ENV_POSTGRES_PASSWORD is not defined"
    exit 1
fi


### Setting date value for the construct name of the backup files ###
NOW=`date '+%Y-%m-%d_%H%M%S'`


### Database name parameter that must be given to the script to generate the backup files of the database given ###
database="$1"
if [ -z "$database" ]; then
    echo "ERROR: No database"
    echo "Usage: $0 <database>"
    exit 1
fi


### Setting logfile value for the backup.log file generated ###
logfile="${database}_${NOW}-backup.log"


### Placing us on the backup directory and sending data to the logfile ###
mkdir -p $HOME/backup
cd $HOME/backup
echo "BACKUP: DATABASE = $database, TIME = $NOW" > $logfile


### Setting the postgress password value ###
db_password=$DB_ENV_POSTGRES_PASSWORD
echo


### Validating the database name given exists for the given postgres user ###
if ! PGPASSWORD="$db_password" /usr/bin/psql -h $DB_PORT_5432_TCP_ADDR -U "$DB_ENV_POSTGRES_USER" -l -F'|' -A "template1" | grep "|$DB_ENV_POSTGRES_USER|" | cut -d'|' -f1 | egrep -q "^$database\$"; then
    echo "ERROR: Database '$database' not found for user '$DB_ENV_POSTGRES_USER'"
    exit 2
fi


### Validating the path for the database name given exists ###
if [ ! -d "$ODOO_DATA_DIR/filestore/$database" ]; then
    echo "ERROR: Filestore '$ODOO_DATA_DIR/filestore/$database' not found"
    exit 3
fi


### Generating the .dump backup file for the given database name ###
echo -n "Backup database: $database ... "
PGPASSWORD="$db_password" /usr/bin/pg_dump -Fc -v -U "$DB_ENV_POSTGRES_USER" --host $DB_PORT_5432_TCP_ADDR -f "${database}_${NOW}.dump" "$database" >> $logfile 2>&1
error=$?; if [ $error -eq 0 ]; then echo "OK"; else echo "ERROR: $error"; fi


### Generating the filestore backup file for the given database name ###
echo -n "Backup filestore: $ODOO_DATA_DIR/filestore/$database ... "
/bin/tar -C "$ODOO_DATA_DIR/filestore" -czf "$HOME/backup/${database}_filestore_${NOW}.tar.gz" $database >> $logfile 2>&1
error=$?
if [ $error -eq 0 ]; then echo "OK"; else echo "ERROR: $error"; fi

### Compressing all the generated backup files into one .tar.gz file ###
echo -n "Compressing backup files: ... "
/bin/tar -czf "${database}_${NOW}.tar.gz" *
error=$?
if [ $error -eq 0 ]; then echo "OK"; else echo "ERROR: $error"; fi
echo ${database}_${NOW}.tar.gz
