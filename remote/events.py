import logging
try:
    import ROOT
except:
    logging.error('Error importing ROOT')

def get_events(file_name):
    logging.info('Getting events for %s' % (file_name))
    try:
        root_file = ROOT.TFile.Open(file_name, 'READ')
        tree = root_file.Get("DQMData")
        return walk(tree)
    except Exception as ex:
        logging.error('Error getting events for %s file: %s' % (file_name, ex))

    return 0

def walk(directory):
    keys = directory.GetListOfKeys()
    for elem in keys:
        elem_name = elem.GetName()
        item = directory.Get(elem_name)
        if item:
            if item.IsFolder():
                if elem_name in ('DQM', 'Run summary', 'TimerService', 'Generator', 'Particles') or elem_name.startswith('Run '):
                    return walk(item)
            else:
                if elem_name in ('nEvt', 'event allocated'):
                    try:
                        return int(item.GetEntries())
                    except Exception as ex:
                        logging.error(ex)

    return 0

