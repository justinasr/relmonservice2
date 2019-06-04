import sqlite3
import os

if os.path.exists('reports.sqlite'):
    os.remove('reports.sqlite')

categories = [entry for entry in os.listdir('.') if os.path.isdir(os.path.join('.', entry))]
conn = sqlite3.connect('reports.sqlite')
c = conn.cursor()
# Create tables
for category in categories:
    print('Creating table for %s' % (category))
    c.execute('CREATE TABLE %s (path text, htmlgz blob);' % (category))
    for root, dirs, files in os.walk(category, topdown=False):
        files_inserted = 0
        for name in files:
            file_path = os.path.join(root, name)
            print(file_path)
            with open(file_path, 'rb') as f:
                ablob = f.read()

            c.execute("INSERT INTO %s VALUES (?, ?)" % (category), [file_path, ablob])
            files_inserted += 1
            if files_inserted % 100 == 0:
                print('Commit after %s inserted files for %s' % (files_inserted, category))
                conn.commit()

        conn.commit()

# Create index
for category in categories:
    print('Creating index for %s' % (category))
    c.execute('CREATE INDEX %sIndex ON %s(path)' % (category, category))

conn.commit()
conn.close()
