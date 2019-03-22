"""
Script takes RelMon config and grid certificates
For RelMons in given config, finds DQMIO datasets, downloads
root files from cmsweb and runs ValidationMatrix from CMSSW
for these root files
During the whole process, it sends callbacks to RelmonService
website about file and whole RelMon status changes
Output is stored in Reports directory
"""
import json
import argparse
import re
from cmswebwrapper import CMSWebWrapper
import logging
import subprocess
import os


def get_root_file_path_for_worflow(workflow_name, cmsweb, category):
    workflow = cmsweb.get_workflow(workflow_name)
    output_datasets = workflow.get('OutputDatasets', [])
    output_datasets = [x for x in output_datasets if '/DQMIO' in x]
    output_dataset = output_datasets[0]
    parts = output_dataset.split('/')[1:]
    dataset = parts[0]
    cmssw = parts[1].split('-')[0]
    PS = '-'.join(parts[1].split('-')[1:])
    dataset_part = dataset + "__" + cmssw + '-' + PS
    if category == 'Data':
        cmsweb_dqm_dir_link = '/dqm/relval/data/browse/ROOT/RelValData/'
    else:
        cmsweb_dqm_dir_link = '/dqm/relval/data/browse/ROOT/RelVal/'

    cmsweb_dqm_dir_link += '_'.join(cmssw.split('_')[:3]) + '_x/'
    response = cmsweb.get(cmsweb_dqm_dir_link)
    HYPERLINK_REGEX = re.compile("href=['\"]([-\._a-zA-Z/\d]*)['\"]")
    hyperlinks = HYPERLINK_REGEX.findall(response)[1:]
    hyperlinks = list(hyperlinks)
    hyperlinks = [x for x in hyperlinks if dataset_part in x]
    return hyperlinks


def read_config(config_filename):
    with open(config_filename) as config_file:
        config = json.load(config_file)

    return config


def notify_about_files(relmon_id, category, list_type, relval):
    try:
        command =  ['curl',
                    '-X',
                    'POST',
                    'http://instance4.cern.ch:8080/update_file',
                    '-s',
                    '-k',
                    '-L',
                    '-m',
                    '60',
                    '-d',
                    '\'%s\'' % (json.dumps({'relmon_id': relmon_id,
                                            'category': category,
                                            'list_type': list_type,
                                            'relval_name': relval['name'],
                                            'file_name': relval['file_name'],
                                            'file_status': relval['file_status'],
                                            'file_size': relval['file_size']})),
                    '-H',
                    '\'Content-Type: application/json\'',
                    '-o',
                    '/dev/null']
        command = ' '.join(command)
        proc = subprocess.Popen(command,
                                shell=True)
        proc.wait()
    except:
        pass


def notify_about_status(relmon_id, relmon_status):
    try:
        command =  ['curl',
                    '-X',
                    'POST',
                    'http://instance4.cern.ch:8080/update_status',
                    '-s',
                    '-k',
                    '-L',
                    '-m',
                    '60',
                    '-d',
                    '\'%s\'' % (json.dumps({'relmon_id': relmon_id,
                                            'relmon_status': relmon_status})),
                    '-H',
                    '\'Content-Type: application/json\'',
                    '-o',
                    '/dev/null']
        command = ' '.join(command)
        proc = subprocess.Popen(command,
                                shell=True)
        proc.wait()
    except:
        pass


def download_root_files(config, cmsweb):
    notify_about_status(config['id'], 'downloading')
    for category in config.get('categories', []):
        category_name = category['name']
        reference_list = category.get('lists', {}).get('reference', {})
        target_list = category.get('lists', {}).get('target', {})
        for reference in reference_list:
            links = get_root_file_path_for_worflow(reference['name'], cmsweb, category_name)
            if len(links) != 0:
                logging.info('Dataset URL %s for %s (reference)' % (links[0], reference['name']))
                reference['file_url'] = links[0]
                reference['file_size'] = 0
                reference['file_status'] = 'downloading'
                reference['file_name'] = reference['file_url'].split('/')[-1]
                notify_about_files(config['id'], category_name, 'reference', reference)
                try:
                    reference['file_name'] = cmsweb.get_big_file(reference['file_url'])
                    reference['file_status'] = 'downloaded'
                    reference['file_size'] = os.path.getsize(reference['file_name'])
                except:
                    logging.error('Error getting %s for %s' % (reference['file_url'], reference['name']))
                    reference['file_status'] = 'error'

                notify_about_files(config['id'], category_name, 'reference', reference)
            else:
                logging.info('No dataset URL %s (reference)' % (reference['name']))
                reference['file_name'] = ''

        for target in target_list:
            links = get_root_file_path_for_worflow(target['name'], cmsweb, category_name)
            if len(links) != 0:
                logging.info('Dataset URL %s for %s (target)' % (links[0], target['name']))
                target['file_url'] = links[0]
                target['file_size'] = 0
                target['file_status'] = 'downloading'
                target['file_name'] = target['file_url'].split('/')[-1]
                notify_about_files(config['id'], category_name, 'target', target)
                try:
                    target['file_name'] = cmsweb.get_big_file(target['file_url'])
                    target['file_status'] = 'downloaded'
                    target['file_size'] = os.path.getsize(target['file_name'])
                except:
                    logging.error('Error getting %s for %s' % (target['file_url'], target['name']))
                    target['file_status'] = 'error'

                notify_about_files(config['id'], category_name, 'target', target)
            else:
                logging.info('No dataset URL %s (target)' % (target['name']))
                target['file_name'] = ''

    logging.info(json.dumps(config, indent=2))
    return config


def get_local_subreport_path(category_name, hlt):
    name = category_name
    if 'PU' in category_name:
        name = name.split('_')[0] + 'Report_PU'
    else:
        name += 'Report'

    if hlt:
        name += '_HLT'

    return name


def get_dataset_lists(category):
    reference_list = category.get('lists', {}).get('reference', {})
    target_list = category.get('lists', {}).get('target', {})
    reference_dataset_list = []
    target_dataset_list = []

    for i in range(min(len(reference_list), len(target_list))):
        if reference_list[i]['file_name'] and target_list[i]['file_name']:
            reference_dataset_list.append(reference_list[i]['file_name'])
            target_dataset_list.append(target_list[i]['file_name'])

        if not reference_list[i]['file_name']:
            logging.error('Downloaded file name is missing for %s, will not compare this workflow' % (reference_list[i]['name']))

        if not  target_list[i]['file_name']:
            logging.error('Downloaded file name is missing for %s, will not compare this workflow' % (reference_list[i]['name']))

    return reference_dataset_list, target_dataset_list


def run_validation_matrix(config):
    notify_about_status(config['id'], 'comparing')
    validation_matrix_log_file = open("validation_matrix.log", "w")
    for category in config.get('categories', []):
        category_name = category['name']
        hlt = category['HLT']
        logging.info('Category: %s' % (category_name))
        logging.info('HLT: %s' % (hlt))
        reference_list, target_list = get_dataset_lists(category)
        if hlt == 'only' or hlt == 'both':
            # Run with HLT
            command = ["ValidationMatrix.py",
                       "-R", ','.join(reference_list),
                       "-T", ','.join(target_list),
                       "-o", get_local_subreport_path(category_name, True),
                       "-N 4",
                       "--hash_name",
                       "--HLT",
                       ";",
                       "mv",
                       get_local_subreport_path(category_name, True),
                       "Reports/"]

            command = ' '.join(command)
            logging.info('ValidationMatrix command: %s' % (command))
            proc = subprocess.Popen(command,
                                    stdout=validation_matrix_log_file,
                                    stderr=validation_matrix_log_file,
                                    shell=True)
            proc.wait()


        if hlt == 'no' or hlt == 'both' and category_name.lower() != 'generator':
            # Run without HLT for everything, except generator
            command = ["ValidationMatrix.py",
                       "-R", ','.join(reference_list),
                       "-T", ','.join(target_list),
                       "-o", get_local_subreport_path(category_name, False),
                       "-N 4",
                       "--hash_name",
                       ";",
                       "mv",
                       get_local_subreport_path(category_name, False),
                       "Reports/"]

            command = ' '.join(command)
            logging.info('ValidationMatrix command: %s' % (command))
            proc = subprocess.Popen(command,
                                    stdout=validation_matrix_log_file,
                                    stderr=validation_matrix_log_file,
                                    shell=True)
            proc.wait()

    notify_about_status(config['id'], 'done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ROOT file downloader and ValidationMatrix runner')
    parser.add_argument('--config')
    parser.add_argument('--cert')
    parser.add_argument('--key')
    args = vars(parser.parse_args())
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

    cert_file = args.get('cert')
    key_file = args.get('key')
    config_filename = args.get('config')
    if not cert_file or not key_file or not config:
        logging.error('Missing user certificate or key or config')
    else:
        cmsweb = CMSWebWrapper(cert_file, key_file)
        config = read_config(config_filename)
        config = download_root_files(config, cmsweb)
        run_validation_matrix(config)