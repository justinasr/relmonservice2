import random
from difflib import SequenceMatcher
import logging
import json


categories = [
    {
        "HLT": "no",
        "automatic_pairing": True,
        "name": "FullSim_PU",
        "reference": [
            {
                "file_name": "DQM_V0001_R000000001__RelValZMM_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2ZMM_13_PU25ns__rsb_190301_174933_1743",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValTTbar_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2TTbar_13_PU25ns__rsb_190301_174927_2163",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValH125GGgluonfusion_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2H125GGgluonfusion_13_PU25ns__rsb_190301_174943_6003",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValQQH1352T_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2QQH1352T_13_PU25ns__rsb_190301_175024_3505",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValNuGun__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2NuGun_PU25ns__rsb_190301_175009_6260",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZEE_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2ZEE_13_PU25ns__rsb_190301_175004_4760",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValSMS-T1tttt_mGl-1500_mLSP-100_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2SMS-T1tttt_mGl-1500_mLSP-100_13_PU25ns__rsb_190301_175030_7874",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZTT_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_rsb-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2ZTT_13_PU25ns__rsb_190301_175018_9215",
            }
        ],
        "target": [
            {
                "file_name": "DQM_V0001_R000000001__RelValZMM_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2ZMM_13UP18_PUpmx25ns__190304_032111_2342",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValTTbar_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2TTbar_13UP18_PUpmx25ns__190304_032127_9125",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValH125GGgluonfusion_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2H125GGgluonfusion_13UP18_PUpmx25ns__190304_032131_7603",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValQQH1352T_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2QQH1352T_13UP18_PUpmx25ns__190304_032137_711",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValNuGun__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2NuGun_UP18_PUpmx25ns__190304_032140_9399",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZEE_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2ZEE_13UP18_PUpmx25ns__190304_032144_2672",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValSMS-T1tttt_mGl-1500_mLSP-100_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2SMS-T1tttt_mGl-1500_mLSP-100_13UP18_PUpmx25ns__190304_032147_8707",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZTT_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2-v1__DQMIO.root",
                "name": "chayanit_RVCMSSW_10_5_0_pre2ZTT_13UP18_PUpmx25ns__190304_032150_8937",
            }
        ]
    },
    {
        "HLT": "no",
        "automatic_pairing": True,
        "name": "FastSim_PU",
        "reference": [
            {
                "file_name": "DQM_V0001_R000000001__RelValZEE_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2ZEE_13_PU25ns__FastSim_190223_163240_1511",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZMM_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2ZMM_13_PU25ns__FastSim_190223_163219_6135",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZTT_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2ZTT_13_PU25ns__FastSim_190223_163209_5526",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValH125GGgluonfusion_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2H125GGgluonfusion_13_PU25ns__FastSim_190223_163223_2419",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValNuGun_UP18__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2NuGun_UP18_PU25ns__FastSim_190223_163230_2043",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValQCD_FlatPt_15_3000HS_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2QCD_FlatPt_15_3000HS_13_PU25ns__FastSim_190223_163236_3435",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValSMS-T1tttt_mGl-1500_mLSP-100_13__CMSSW_10_5_0_pre2-PU25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2SMS-T1tttt_mGl-1500_mLSP-100_13_PU25ns__FastSim_190223_163226_6722",
            }
        ],
        "target": [
            {
                "file_name": "DQM_V0001_R000000001__RelValZEE_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2ZEE_13_PUpmx25ns__FastSim_190226_152133_5575",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZTT_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2ZTT_13_PUpmx25ns__FastSim_190226_152142_4060",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValZMM_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2ZMM_13_PUpmx25ns__FastSim_190226_152137_6232",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValH125GGgluonfusion_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2H125GGgluonfusion_13_PUpmx25ns__FastSim_190226_152146_7018",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValQCD_FlatPt_15_3000HS_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2QCD_FlatPt_15_3000HS_13_PUpmx25ns__FastSim_190226_152153_9364",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValNuGun_UP18__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2NuGun_UP18_PUpmx25ns__FastSim_190226_152149_9182",
            },
            {
                "file_name": "DQM_V0001_R000000001__RelValSMS-T1tttt_mGl-1500_mLSP-100_13__CMSSW_10_5_0_pre2-PUpmx25ns_105X_upgrade2018_realistic_v2_FastSim-v1__DQMIO.root",
                "name": "nwickram_RVCMSSW_10_5_0_pre2SMS-T1tttt_mGl-1500_mLSP-100_13_PUpmx25ns__FastSim_190226_152157_2540",
            }
        ]
    }
]


def get_important_part(filne_name):
    return filne_name.split('__')[1] + '_' + filne_name.split("__")[2].split("-")[1]


def match(references, targets):
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


for category in categories:
    reference = [x['file_name'] for x in category['reference']]
    target = [x['file_name'] for x in category['target']]
    # random.shuffle(reference)
    random.shuffle(target)
    print('Will match references:\n%s' % json.dumps(reference, indent=2))
    print('Will match targets:\n%s' % json.dumps(target, indent=2))
    reference, target = match(reference, target)
    print('Mathced references:\n%s' % json.dumps(reference, indent=2))
    print('Mathced targets:\n%s' % json.dumps(target, indent=2))
