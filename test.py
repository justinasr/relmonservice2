import json
import downloader

with open('requests.json') as f:
    data = json.load(f)

cert = '/afs/cern.ch/user/j/jrumsevi/private/user.crt.pem'
key = '/afs/cern.ch/user/j/jrumsevi/private/user.key.pem'

for d in data:
    print('Name: %s' % d['name'])
    for category in d.get('categories', []):
        print('  %s' % (category['name']))
        for ref in category['lists']['reference']:
            print('    %s' % (ref['name']))
            links = downloader.get_root_file_path_for_worflow(ref['name'], cert, key, category['name'])
            if len(links) == 1:
                print('    %s' % (links[0]))
            elif len(links) == 0:
                print('    No dataset found!')
            else:
                print('    More than one dataset %s' % (links))

        for tar in category['lists']['target']:
            print('    %s' % (tar['name']))
            links = downloader.get_root_file_path_for_worflow(tar['name'], cert, key, category['name'])
            if len(links) == 1:
                print('    %s' % (links[0]))
            elif len(links) == 0:
                print('    No dataset found!')
            else:
                print('    More than one dataset %s' % (links))
