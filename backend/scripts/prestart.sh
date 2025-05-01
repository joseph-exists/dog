#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# ensure pgai init - this doesn't work the way it's written
# psql -U $POSTGRES_USER -d $POSTGRES_DB -c "CREATE EXTENSION IF NOT EXISTS ai CASCADE;"

# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py
