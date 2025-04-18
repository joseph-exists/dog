#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# ensure pgai init - need to move this later
# echo 'psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS ai CASCADE;"' >> backend/scripts/prestart.sh


# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py
