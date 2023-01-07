import mysql.connector
import sqlite3
import uuid


class MySQLProxy:

    def __init__(self, mysql_db_name, mysql_db_user, mysql_db_password, mysql_db_host, mysql_db_port):
        self.mysql_db_name = mysql_db_name
        self.mysql_db_user = mysql_db_user
        self.mysql_db_password = mysql_db_password
        self.mysql_db_host = mysql_db_host
        self.mysql_db_port = mysql_db_port

    def convert(self):
        # Connect to the MySQL database
        mysql_conn = mysql.connector.connect(user=self.mysql_db_user,
                                             password=self.mysql_db_password,
                                             host=self.mysql_db_host,
                                             port=self.mysql_db_port,
                                             database=self.mysql_db_name)

        mysql_cursor = mysql_conn.cursor()

        # Connect to the SQLite database
        sqlite_name = {str(uuid.uuid4().hex)}.sqlite
        sqlite_db_path = f'./database/{sqlite_name}'
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
        mysql_conn.close()
        sqlite_conn.close()
        return sqlite_name
