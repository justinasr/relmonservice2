"""
Convert directories with htmlgz files to SQLite database
"""
import sqlite3
import os


categories = [entry for entry in os.listdir('.') if os.path.isdir(os.path.join('.', entry))]
db_connection = sqlite3.connect('reports.sqlite')
db_cursor = db_connection.cursor()
indexes_to_create = []

for category in categories:
    # Create tables
    print('Creating table for %s' % (category))
    db_cursor.execute('DROP TABLE IF EXISTS %s;' % (category))
    db_cursor.execute('CREATE TABLE %s (path text, htmlgz blob);' % (category))
    # Walk through files and add to database
    for root, dirs, files in os.walk(category, topdown=False):
        files_inserted = 0
        for name in files:
            file_path = os.path.join(root, name)
            with open(file_path, 'rb') as f:
                ablob = f.read()

            db_cursor.execute("INSERT INTO %s VALUES (?, ?)" % (category), [file_path, ablob])
            files_inserted += 1
            if files_inserted % 1000 == 0:
                print('Commit after %s inserted files for %s' % (files_inserted, category))
                db_connection.commit()

        print('Commit after %s inserted files for %s' % (files_inserted, category))
        db_connection.commit()

    if files_inserted == 0:
        print('No files were inserted for %s, dropping empty table' % (category))
        db_cursor.execute('DROP TABLE IF EXISTS %s;' % (category))
        db_connection.commit()
    else:
        indexes_to_create.append(category)

# Create index
for category in indexes_to_create:
    print('Creating index for %s' % (category))
    db_cursor.execute('CREATE INDEX %sIndex ON %s(path)' % (category, category))

db_connection.commit()
db_connection.close()
