"""
Convert directories with htmlgz files to SQLite database
"""
import sqlite3
import os


if os.path.exists('reports.sqlite'):
    os.remove('reports.sqlite')

CATEGORIES = [entry for entry in os.listdir('.') if os.path.isdir(os.path.join('.', entry))]
DB_CONNECTION = sqlite3.connect('reports.sqlite')
DB_CURSOR = DB_CONNECTION.cursor()
for category in CATEGORIES:
    # Create tables
    print('Creating table for %s' % (category))
    DB_CURSOR.execute('CREATE TABLE %s (path text, htmlgz blob);' % (category))
    # Walk through files and add to database
    for root, dirs, files in os.walk(category, topdown=False):
        files_inserted = 0
        for name in files:
            file_path = os.path.join(root, name)
            with open(file_path, 'rb') as f:
                ablob = f.read()

            DB_CURSOR.execute("INSERT INTO %s VALUES (?, ?)" % (category), [file_path, ablob])
            files_inserted += 1
            if files_inserted % 1000 == 0:
                print('Commit after %s inserted files for %s' % (files_inserted, category))
                DB_CONNECTION.commit()

        print('Commit after %s inserted files for %s' % (files_inserted, category))
        DB_CONNECTION.commit()

# Create index
for category in CATEGORIES:
    print('Creating index for %s' % (category))
    DB_CURSOR.execute('CREATE INDEX %sIndex ON %s(path)' % (category, category))

DB_CONNECTION.commit()
DB_CONNECTION.close()
