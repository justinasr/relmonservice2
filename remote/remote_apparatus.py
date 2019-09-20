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
import logging
import subprocess
import os
import time
import sys
from difflib import SequenceMatcher
from cmswebwrapper import CMSWebWrapper


__CALLBACK_URL = 'http://instance3.cern.ch/relmonsvc/update'


def get_workflow(workflow_name, cmsweb):
    """
    Get workflow from cmsweb
    """
    workflow = cmsweb.get_workflow(workflow_name)
    return workflow


def get_dqmio_dataset(workflow):
    """
    Given a workflow dictionary, return first occurence of DQMIO string
    Return None if it could not be found
    """
    output_datasets = workflow.get('OutputDatasets', [])
    for dataset in output_datasets:
        if '/DQMIO' in dataset:
            return dataset

    return None


def get_root_file_path_for_dataset(dqmio_dataset, cmsweb, category_name):
    logging.info('Getting root file path for dataset %s. Category %s', dqmio_dataset, category_name)
    parts = dqmio_dataset.split('/')[1:]
    dataset = parts[0]
    cmssw = parts[1].split('-')[0]
    processing_string = parts[1].split('-')[1]
    dataset_part = dataset + "__" + cmssw + '-' + processing_string
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
    hyperlinks = sorted(hyperlinks)
    logging.info('Selected hyperlinks %s', json.dumps(hyperlinks, indent=2))
    return hyperlinks


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
                   '--cookie cookie.txt',
                   __CALLBACK_URL,
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
        logging.info('Notifying...')
        proc = subprocess.Popen(command,
                                shell=True)
        proc.wait()
        os.remove('notify_data.json')
    except Exception as ex:
        logging.error('Error while doing notifying: %s' % (ex))
        pass

    time.sleep(0.05)


def download_root_files(relmon, cmsweb):
    """
    Download all files needed for comparison and fill relmon dictionary
    """
    for category in relmon.get('categories', []):
        category_name = category['name']
        reference_list = category.get('reference', [])
        target_list = category.get('target', [])
        for item in reference_list + target_list:
            # if os.path.isfile(item.get('file_name', 'no-file-name')):
            #     item['file_size'] = os.path.getsize(item['file_name'])
            #     item['status'] = 'downloaded'
            #     notify(relmon)
            #     continue

            workflow = get_workflow(item['name'], cmsweb)
            if not workflow:
                item['status'] = 'no_workflow'
                notify(relmon)
                logging.warning('Could not find workflow %s in ReqMgr2', item['name'])
                continue

            dqmio_dataset = get_dqmio_dataset(workflow)
            if not dqmio_dataset:
                item['status'] = 'no_dqmio'
                notify(relmon)
                logging.warning('Could not find DQMIO dataset in %s. Datasets: %s',
                                item['name'],
                                ', '.join(workflow.get('OutputDatasets', [])))
                continue

            file_urls = get_root_file_path_for_dataset(dqmio_dataset, cmsweb, category_name)
            if not file_urls:
                item['status'] = 'no_root'
                notify(relmon)
                logging.warning('Could not get root file path for %s dataset of %s workflow',
                                dqmio_dataset,
                                item['name'])
                continue

            item['versioned'] = len(file_urls) > 1
            file_url = file_urls[-1]

            logging.info('File URL for %s is %s', item['name'], file_url)
            item['file_url'] = file_url
            item['file_size'] = 0
            item['status'] = 'downloading'
            item['file_name'] = item['file_url'].split('/')[-1]
            notify(relmon)
            try:
                item['file_name'] = cmsweb.get_big_file(item['file_url'])
                item['status'] = 'downloaded'
                item['file_size'] = os.path.getsize(item['file_name'])
                logging.info('Downloaded %s. Size %.2f MB',
                             item['file_name'],
                             item.get('file_size', 0) / 1024.0 / 1024.0)
            except Exception as ex:
                logging.error(ex)
                logging.error('Error getting %s for %s', item['file_url'], item['name'])
                item['status'] = 'failed'

            notify(relmon)

    return relmon


def get_local_subreport_path(category_name, hlt):
    """
    Return name of local folder
    Basically add Report and HLT to category name
    """
    name = category_name
    if 'PU' in category_name:
        name = name.split('_')[0] + 'Report_PU'
    else:
        name += 'Report'

    if hlt:
        name += '_HLT'

    return name


def get_important_part(file_name):
    return file_name.split('__')[1] + '_' + file_name.split("__")[2].split("-")[1]


def make_file_tree(items, category):
    result_tree = {}
    for item in items:
        filename = item['file_name']
        dataset = filename.split('__')[1]
        if category == 'Data':
            run_number = filename.split('__')[0].split('_')[-1]
        else:
            run_number = 'all_runs'

        if dataset not in result_tree:
            result_tree[dataset] = {}

        if run_number not in result_tree[dataset]:
            result_tree[dataset][run_number] = []

        result_tree[dataset][run_number].append(item)

    return result_tree


def pair_references_with_targets(category):
    logging.info('Will try to automatically find pairs in %s', category['name'])
    references = category.get('reference', [])
    targets = category.get('target', [])
    reference_tree = make_file_tree(references, category['name'])
    target_tree = make_file_tree(targets, category['name'])

    logging.info('References tree: %s', json.dumps(reference_tree, indent=4))
    logging.info('Targets tree: %s', json.dumps(target_tree, indent=4))

    selected_pairs = []

    for reference_dataset, reference_runs in reference_tree.items():
        for reference_run, references_in_run in reference_runs.items():
            targets_in_run = target_tree.get(reference_dataset, {}).get(reference_run, [])
            if len(references_in_run) == 1 and len(targets_in_run) == 1:
                reference = references_in_run.pop()
                target = targets_in_run.pop()
                reference_name = reference['file_name']
                target_name = target['file_name']
                logging.info('Pair %s with %s', reference_name, target_name)
                selected_pairs.append((reference_name, target_name))
            else:
                logging.info('Dataset %s. Run %s. Will try to match %s\nwith\n%s',
                             reference_dataset,
                             reference_run,
                             json.dumps(references_in_run, indent=2),
                             json.dumps(targets_in_run, indent=2))

                all_ratios = []
                for reference in references_in_run:
                    for target in targets_in_run:
                        reference_string = get_important_part(reference['file_name'])
                        target_string = get_important_part(target['file_name'])
                        ratio = SequenceMatcher(a=reference_string, b=target_string).ratio()
                        reference_target_ratio = (reference, target, ratio)
                        all_ratios.append(reference_target_ratio)
                        logging.info('%s %s -> %s' % (reference_string, target_string, ratio))

                used_references = set()
                used_targets = set()
                all_ratios.sort(key=lambda x: x[2], reverse=True)
                for reference_target_ratio in all_ratios:
                    reference_name = reference_target_ratio[0]['file_name']
                    target_name = reference_target_ratio[1]['file_name']
                    similarity_ratio = reference_target_ratio[2]
                    if reference_name not in used_references and target_name not in used_targets:
                        logging.info('Pair %s with %s. Similarity %.3f',
                                     reference_name,
                                     target_name,
                                     similarity_ratio)
                        used_references.add(reference_name)
                        used_targets.add(target_name)
                        references_in_run.remove(reference_target_ratio[0])
                        targets_in_run.remove(reference_target_ratio[1])
                        selected_pairs.append((reference_name, target_name))

            for reference in references_in_run:
                if reference['status'] == 'downloaded':
                    reference['status'] = 'no_match'

            for target in targets_in_run:
                if target['status'] == 'downloaded':
                    target['status'] = 'no_match'

    logging.info('References leftovers tree: %s', json.dumps(reference_tree, indent=4))
    logging.info('Targets leftovers tree: %s', json.dumps(target_tree, indent=4))

    sorted_references = [x[0] for x in selected_pairs]
    sorted_targets = [x[1] for x in selected_pairs]

    return sorted_references, sorted_targets


def get_dataset_lists(category):
    """
    Return lists of files to compare
    Automatically paired if automatic pairing is enabled
    """
    reference_list = category.get('reference', {})
    target_list = category.get('target', {})
    reference_dataset_list = []
    target_dataset_list = []
    automatic_pairing = category['automatic_pairing']

    if automatic_pairing:
        reference_dataset_list, target_dataset_list = pair_references_with_targets(category)
    else:
        for i in range(min(len(reference_list), len(target_list))):
            if reference_list[i]['file_name'] and target_list[i]['file_name']:
                reference_dataset_list.append(reference_list[i]['file_name'])
                target_dataset_list.append(target_list[i]['file_name'])

            if not reference_list[i]['file_name']:
                logging.error('Downloaded file name is missing for %s, will not compare this workflow',
                              reference_list[i]['name'])

            if not target_list[i]['file_name']:
                logging.error('Downloaded file name is missing for %s, will not compare this workflow',
                              reference_list[i]['name'])

    return reference_dataset_list, target_dataset_list


def compare_compress_move(category_name, hlt, reference_list, target_list, log_file, cpus):
    """
    The main function that compares, compresses and moves reports to Reports directory
    """
    subreport_path = get_local_subreport_path(category_name, hlt)
    comparison_command = ' '.join(['ValidationMatrix.py',
                                   '-R',
                                   ','.join(reference_list),
                                   '-T',
                                   ','.join(target_list),
                                   '-o',
                                   subreport_path,
                                   '-N %s' % (cpus),
                                   '--hash_name',
                                   '--HLT' if hlt else ''])

    # Remove all /cms-service-reldqm/style/blueprint/ from HTML files
    path_fix_command = "find %s/ -type f -name '*.html' | xargs -L1 sed -i -e 's#/cms-service-reldqm/style/blueprint/##g'" % (subreport_path)
    compression_command = ' '.join(['dir2webdir.py', subreport_path])
    move_command = ' '.join(['mv', subreport_path, 'Reports/'])

    logging.info('ValidationMatrix command: %s' % (comparison_command))
    proc = subprocess.Popen(comparison_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.communicate()

    logging.info('Path fix command: %s' % (path_fix_command))
    proc = subprocess.Popen(path_fix_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.communicate()

    logging.info('Compression command: %s' % (compression_command))
    proc = subprocess.Popen(compression_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.communicate()

    logging.info('Move command: %s' % (move_command))
    proc = subprocess.Popen(move_command,
                            stdout=log_file,
                            stderr=log_file,
                            shell=True)
    proc.communicate()


def run_validation_matrix(config, cpus):
    """
    Iterate through categories and start comparison process
    """
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
            compare_compress_move(category_name, True, reference_list, target_list, log_file, cpus)

        if hlt == 'no' or hlt == 'both' and category_name.lower() != 'generator':
            # Run without HLT for everything, except generator
            compare_compress_move(category_name, False, reference_list, target_list, log_file, cpus)

        category['status'] = 'done'
        notify(config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ROOT file downloader and ValidationMatrix runner')
    parser.add_argument('--relmon', '-r')
    parser.add_argument('--cert', '-c')
    parser.add_argument('--key', '-k')
    parser.add_argument('--cpus', nargs='?', const=1, type=int)
    parser.add_argument('--notifyfinished', action='store_true')
    args = vars(parser.parse_args())
    logging.basicConfig(stream=sys.stdout, format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

    cert_file = args.get('cert')
    key_file = args.get('key')
    relmon_filename = args.get('relmon')
    cpus = args.get('cpus', 1)
    if cpus:
        cpus = int(cpus)
    else:
        cpus = 1

    notify_finished = bool(args.get('notifyfinished'))
    logging.info('Arguments: relmon %s; cert %s; key %s; cpus %s; notify-finished %s',
                 relmon_filename,
                 cert_file,
                 key_file,
                 cpus,
                 'YES' if notify_finished else 'NO')
    try:
        relmon = read_relmon(relmon_filename)
        if notify_finished:
            if relmon['status'] != 'failed':
                relmon['status'] = 'finished'
        else:
            cmsweb = CMSWebWrapper(cert_file, key_file)
            relmon['status'] = 'running'
            notify(relmon)
            relmon = download_root_files(relmon, cmsweb)
            run_validation_matrix(relmon, cpus)
            relmon['status'] = 'finishing'
            with open(relmon_filename, 'w') as relmon_file:
                json.dump(relmon, relmon_file, indent=4)
    except Exception as ex:
        logging.error(ex)
        relmon['status'] = 'failed'

    notify(relmon)
