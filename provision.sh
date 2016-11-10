APP_DB_USER=hackweek
APP_DB_PASS=hackweek
APP_DB_NAME=$APP_DB_USER

sudo apt-get install -y redis-server postgresql postgis* libpq-dev python3-pip

cat << EOF | su - postgres -c psql
-- Create the database user:
CREATE USER $APP_DB_USER WITH PASSWORD '$APP_DB_PASS';

-- Create the database:
CREATE DATABASE $APP_DB_NAME WITH OWNER=$APP_DB_USER
                                  LC_COLLATE='en_US.utf8'
                                  LC_CTYPE='en_US.utf8'
                                  ENCODING='UTF8'
                                  TEMPLATE=template0;
EOF

su - postgres psql -c "CREATE EXTENSION postgis; CREATE EXTENSION postgis_topology;" $APP_DB_NAME

pip3 install -r /vagrant/requirements.txt

echo "Your PostgreSQL database has been setup"
echo "  Database: $APP_DB_NAME"
echo "  Username: $APP_DB_USER"
echo "  Password: $APP_DB_PASS"
echo ""
echo "Admin access to postgres user via VM:"
echo "  vagrant ssh"
echo "  sudo su - postgres"
echo ""
echo "psql access to app database user via VM:"
echo "  vagrant ssh"
echo "  sudo su - postgres"
echo "  PGUSER=$APP_DB_USER PGPASSWORD=$APP_DB_PASS psql -h localhost $APP_DB_NAME"
echo ""