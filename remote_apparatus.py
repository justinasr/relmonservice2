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
import time


__callback_url = 'http://instance4.cern.ch:8080/update'


def get_workflow(workflow_name, cmsweb):
    workflow = cmsweb.get_workflow(workflow_name)
    return workflow


def get_dqmio_dataset(workflow):
    output_datasets = workflow.get('OutputDatasets', [])
    output_datasets = [x for x in output_datasets if '/DQMIO' in x]
    if len(output_datasets) > 0:
        return output_datasets[0]
    else:
        return None


def get_root_file_path_for_dataset(dqmio_dataset, cmsweb, category_name):
    parts = dqmio_dataset.split('/')[1:]
    dataset = parts[0]
    cmssw = parts[1].split('-')[0]
    PS = '-'.join(parts[1].split('-')[1:])
    dataset_part = dataset + "__" + cmssw + '-' + PS
    if category_name == 'Data':
        cmsweb_dqm_dir_link = '/dqm/relval/data/browse/ROOT/RelValData/'
    else:
        cmsweb_dqm_dir_link = '/dqm/relval/data/browse/ROOT/RelVal/'

    cmsweb_dqm_dir_link += '_'.join(cmssw.split('_')[:3]) + '_x/'
    response = cmsweb.get(cmsweb_dqm_dir_link)
    hyperlink_regex = re.compile("href=['\"]([-\._a-zA-Z/\d]*)['\"]")
    hyperlinks = hyperlink_regex.findall(response)[1:]
    hyperlinks = list(hyperlinks)
    hyperlinks = [x for x in hyperlinks if dataset_part in x]
    if len(hyperlinks) > 0:
        return hyperlinks[0]
    else:
        return None


def read_relmon(relmon_filename):
    with open(relmon_filename) as relmon_file:
        relmon = json.load(relmon_file)

    return relmon


def notify(relmon):
    try:
        command = ['curl',
                   '-X',
                   'POST',
                   __callback_url,
                   '-s',
                   '-k',
                   '-L',
                   '-m',
                   '60',
                   '-d',
                   '\'%s\'' % (json.dumps(relmon)),
                   '-H',
                   '\'Content-Type: application/json\'',
                   '-o',
                   '/dev/null']
        command = ' '.join(command)
        proc = subprocess.Popen(command,
                                shell=True)
        proc.wait()
    except Exception as ex:
        logging.error(ex)
        pass

    time.sleep(1)


def download_root_files(relmon, cmsweb):
    for category in relmon.get('categories', []):
        category_name = category['name']
        reference_list = category.get('reference', [])
        target_list = category.get('target', [])
        for item in reference_list + target_list:
            workflow = get_workflow(item['name'], cmsweb)
            if not workflow:
                item['status'] = 'no_workflow'
                notify(relmon)
                continue

            dqmio_dataset = get_dqmio_dataset(workflow)
            if not dqmio_dataset:
                item['status'] = 'no_dqmio'
                notify(relmon)
                continue

            file_url = get_root_file_path_for_dataset(dqmio_dataset, cmsweb, category_name)
            if not file_url:
                item['status'] = 'no_root'
                notify(relmon)
                continue

            logging.info('Dataset URL %s for %s' % (file_url, item['name']))
            item['file_url'] = file_url
            item['file_size'] = 0
            item['status'] = 'downloading'
            item['file_name'] = item['file_url'].split('/')[-1]
            notify(relmon)
            try:
                item['file_name'] = cmsweb.get_big_file(item['file_url'])
                item['status'] = 'downloaded'
                item['file_size'] = os.path.getsize(item['file_name'])
            except Exception as ex:
                logging.error(ex)
                logging.error('Error getting %s for %s' % (item['file_url'], item['name']))
                item['status'] = 'failed'

            notify(relmon)

    logging.info(json.dumps(relmon, indent=2))
    return relmon


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
    reference_list = category.get('reference', {})
    target_list = category.get('target', {})
    reference_dataset_list = []
    target_dataset_list = []

    for i in range(min(len(reference_list), len(target_list))):
        if reference_list[i]['file_name'] and target_list[i]['file_name']:
            reference_dataset_list.append(reference_list[i]['file_name'])
            target_dataset_list.append(target_list[i]['file_name'])

        if not reference_list[i]['file_name']:
            logging.error('Downloaded file name is missing for %s, will not compare this workflow' % (reference_list[i]['name']))

        if not target_list[i]['file_name']:
            logging.error('Downloaded file name is missing for %s, will not compare this workflow' % (reference_list[i]['name']))

    return reference_dataset_list, target_dataset_list


def run_validation_matrix(config):
    validation_matrix_log_file = open("validation_matrix.log", "w")
    for category in config.get('categories', []):
        category_name = category['name']
        hlt = category['HLT']
        logging.info('Category: %s' % (category_name))
        logging.info('HLT: %s' % (hlt))
        reference_list, target_list = get_dataset_lists(category)
        category['status'] = 'comparing'
        notify(config)
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

        category['status'] = 'done'
        notify(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ROOT file downloader and ValidationMatrix runner')
    parser.add_argument('--relmon')
    parser.add_argument('--cert')
    parser.add_argument('--key')
    args = vars(parser.parse_args())
    logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

    cert_file = args.get('cert')
    key_file = args.get('key')
    relmon_filename = args.get('relmon')
    if not cert_file or not key_file or not relmon_filename:
        logging.error('Missing user certificate or key or relmon file')
    else:
        try:
            cmsweb = CMSWebWrapper(cert_file, key_file)
            relmon = read_relmon(relmon_filename)
            relmon['status'] = 'running'
            notify(relmon)
            relmon = download_root_files(relmon, cmsweb)
            run_validation_matrix(relmon)
            relmon['status'] = 'finished'
        except Exception as ex:
            logging.error(ex)
            relmon['status'] = 'failed'

        notify(relmon)
