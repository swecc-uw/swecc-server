@echo off

if "%~1"=="" (
    echo Username argument is required.
    exit 1
) else (
    set "username=%~1"
)

set "SQL_QUERY=update members_user set is_superuser = 't' where username = '%username%'; update members_user set is_staff = 't' where username = '%username%';"

docker exec -it swecc-server-db-1 psql -U root postgres -c "%SELECT_QUERY%"

echo User '%username%' is now an admin.