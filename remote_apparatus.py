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
from difflib import SequenceMatcher


__callback_url = 'http://instance4.cern.ch:8080/update'
__number_of_threads = 4


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
        with open('notify_data.json', 'w') as json_file:
            json.dump(relmon, json_file, indent=2, sort_keys=True)

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
                   '@notify_data.json',
                   '-H',
                   '\'Content-Type: application/json\'',
                   '-o',
                   '/dev/null']
        command = ' '.join(command)
        logging.info('Notify command: %s' % (command))
        logging.info('curl callback length %s' % (len(command)))
        proc = subprocess.Popen(command,
                                shell=True)
        proc.wait()
        os.remove('notify_data.json')
    except Exception as ex:
        logging.error('Error while doing notifying: %s' % (ex))
        pass

    time.sleep(0.1)


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
                logging.info('Downloaded %s. Size %s MB' % (item['file_name'], item.get('file_size', 0) / 1024.0 / 1024.0))
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


def get_important_part(filne_name):
    return filne_name.split('__')[1] + '_' + filne_name.split("__")[2].split("-")[1]


def pair_references_with_targets(references, targets):
    if len(references) != len(targets):
        logging.error('Cannot do automatic pairing for different length lists')
        return references, targets

    all_ratios = []
    for reference in references:
        for target in targets:
            reference_string = get_important_part(reference)
            target_string = get_important_part(target)
            ratio = SequenceMatcher(a=reference_string, b=target_string).ratio()
            reference_target_ratio = (reference, target, ratio)
            all_ratios.append(reference_target_ratio)
            logging.info('%s %s -> %s' % (reference_string, target_string, ratio))

    used_references = set()
    used_targets = set()
    all_ratios.sort(key=lambda x: x[2], reverse=True)
    selected_pairs = []
    for reference_target_ratio in all_ratios:
        reference_name = reference_target_ratio[0]
        target_name = reference_target_ratio[1]
        if reference_name not in used_references and target_name not in used_targets:
            selected_pairs.append(reference_target_ratio)
            used_references.add(reference_name)
            used_targets.add(target_name)

    sorted_references = [x[0] for x in selected_pairs]
    sorted_targets = [x[1] for x in selected_pairs]
    if len(sorted_references) != len(references) or len(sorted_targets) != len(targets):
        logging.error('Mismatch of number of references or targets after matching')
        return references, targets

    return sorted_references, sorted_targets


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

    automatic_pairing = category['automatic_pairing']
    if automatic_pairing:
        reference_dataset_list, target_dataset_list = pair_references_with_targets(reference_dataset_list, target_dataset_list)

    return reference_dataset_list, target_dataset_list


def compare_compress_move(category_name, HLT, reference_list, target_list, log_file):
    subreport_path = get_local_subreport_path(category_name, HLT)
    comparison_command = ' '.join(['ValidationMatrix.py',
                                   '-R',
                                   ','.join(reference_list),
                                   '-T',
                                   ','.join(target_list),
                                   '-o',
                                   subreport_path,
                                   '-N %s' % (__number_of_threads),
                                   '--hash_name',
                                   '--HLT' if HLT else ''])

    compression_command = ' '.join(['dir2webdir.py', subreport_path])
    move_command = ' '.join(['mv', subreport_path, 'Reports/'])

    logging.info('ValidationMatrix command: %s' % (comparison_command))
    proc = subprocess.Popen(comparison_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.wait()

    logging.info('Compression command: %s' % (compression_command))
    proc = subprocess.Popen(compression_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.wait()

    logging.info('Move command: %s' % (move_command))
    proc = subprocess.Popen(move_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.wait()


def run_validation_matrix(config):
    log_file = open("validation_matrix.log", "w")
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
            compare_compress_move(category_name, True, reference_list, target_list, log_file)

        if hlt == 'no' or hlt == 'both' and category_name.lower() != 'generator':
            # Run without HLT for everything, except generator
            compare_compress_move(category_name, False, reference_list, target_list, log_file)

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
            relmon['status'] = 'finishing'
        except Exception as ex:
            logging.error(ex)
            relmon['status'] = 'failed'

        notify(relmon)
