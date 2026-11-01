# Database outage

Check `docker compose ps postgres` and `docker compose logs --tail=100 postgres backend`. Preserve db_data. After repairing the local database, run `docker compose up -d --wait postgres backend` and `make smoke`. The runtime agent cannot administer PostgreSQL. Database request errors are traced; automatic remediation is limited to the isolated workflow dependency.
