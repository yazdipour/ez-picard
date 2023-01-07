import mysql.connector
import sqlite3
import uuid
import re


class MySQLProxy:

    def __init__(self, connection_string):
        if not connection_string:
            raise ValueError("Connection string is empty")

        # Compile the regular expression pattern
        pattern = re.compile(
            r"mysql://(?P<user>.+):(?P<password>.+)@(?P<host>.+):(?P<port>\d+)/(?P<database>.+)")

        # Match the connection string against the pattern
        match = pattern.match(connection_string)

        # Extract the individual components from the match object
        config = {
            "host": match["host"],
            "port": int(match["port"]),
            "user": match["user"],
            "password": match["password"],
            "database": match["database"],
        }
        self.mysql_conn = mysql.connector.connect(
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            database=config["database"]
        )

    def convert(self, base_path: str = '/database', sqlite_name=str(uuid.uuid4().hex)):
        mysql_cursor = self.mysql_conn.cursor()
        sqlite_db_path = f'{base_path}/{sqlite_name}/{sqlite_name}.sqlite'
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()

        # Retrieve the list of tables in the MySQL database
        mysql_cursor.execute("SHOW TABLES")
        tables = mysql_cursor.fetchall()
        # Iterate through the list of tables and create them in the SQLite database
        for table in tables:
            table_name = table[0]

            # Retrieve the structure of the table
            mysql_cursor.execute(f"DESCRIBE {table_name}")
            structure = mysql_cursor.fetchall()

            # Create the table in the SQLite database
            sql = f"CREATE TABLE {table_name} ("
            for column in structure:
                column_name = column[0]
                column_type = column[1]
                sql += f"{column_name} {column_type}, "
            sql = f"{sql[:-2]})"
            sqlite_cursor.execute(sql)

        # Save the changes to the SQLite database and close the connections
        sqlite_conn.commit()
        self.mysql_conn.close()
        sqlite_conn.close()
        return sqlite_name
