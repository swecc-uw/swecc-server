echo off

setlocal EnableDelayedExpansion

@REM Function to generate a random string of specified length
set "charset=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
set "length=10"
set "randomString="

for /L %%i in (1,1,%length%) do (
    set /A "index=!random! %% 62"
    for %%j in (!index!) do set "randomString=!randomString!!charset:~%%j,1!"
)

@REM Check if username argument is passed, otherwise generate random username
if "%~1"=="" (
    set "test_username=!randomString!"
) else (
    set "test_username=%~1"
)


@REM docker exec -it swecc-server-db-1 psql -U root postgres -c  "SELECT * FROM members_user;"
set "HashedPassword=pbkdf2_sha256$600000$BjdYGzJ9HB5rWVdRnLRr5l$WblHaqgKgjitB2svIbbTKuVe5BGe2p+7boYh0trY3NE="
set "test_firstname=!test_username!"
set "test_lastname=EJ"
set "email=!randomString!@uw.edu"
set "discord_id=123456789"

:: Get current date and time (timestamp)
set "currentDate=%DATE%"
set "currentTime=%TIME%"

:: Remove unwanted characters from time (colon and period)
set "currentTime=%currentTime::=%"
set "currentTime=%currentTime:.=%"

:: Format date and time as 'YYYY-MM-DD HH:MM:SS'
set "formattedDate=%currentDate:~10,4%-%currentDate:~4,2%-%currentDate:~7,2%"
set "formattedTime=%currentTime:~0,2%:%currentTime:~2,2%:%currentTime:~4,2%"

:: Append milliseconds and timezone (dummy values for batch script)
set "milliseconds=.000000"
set "timezone=+00"

:: Combine to create the final 'date_join' timestamp
set "date_join=%formattedDate% %formattedTime%%milliseconds%%timezone%"

:: Create the SQL query
set "SQL_QUERY=INSERT INTO members_user (username, first_name, last_name, email, discord_username, discord_id, password, is_superuser, is_staff, is_active, date_joined, created) VALUES ('!test_username!', '!test_firstname!', '!test_lastname!', '!email!', '!random_string!', '!discord_id!', '!HashedPassword!', 'f', 'f', 't', '!date_join!', '!date_join!');"
set "SQL_QUERY_INSERT_INTO_VERIFIED_TABLE= INSERT INTO auth_group (id, name) VALUES (1, 'verified') ON CONFLICT DO NOTHING;"
set "SQL_QUERY_INSERT_INTO_USER_GROUP_TABLE= INSERT INTO members_user_groups (user_id, group_id) VALUES ((SELECT id FROM members_user WHERE username = '!test_username!'), 1) ON CONFLICT DO NOTHING;"

docker exec -it swecc-server-db-1 psql -U root postgres -c  "%SQL_QUERY%"
docker exec -it swecc-server-db-1 psql -U root postgres -c  "%SQL_QUERY_INSERT_INTO_VERIFIED_TABLE%"
docker exec -it swecc-server-db-1 psql -U root postgres -c  "%SQL_QUERY_INSERT_INTO_USER_GROUP_TABLE%"

echo User created successfully. Username: !test_username!, Email: !email!
