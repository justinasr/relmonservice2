# RelMonService2

## Introduction

RelMonService2 is a service that takes user given workflow names (ReqMgr2 request names), downloads DQMIO datasets, feeds them to `runTheMatrix.py` and moves generated reports to user accessible reports website. This is a second version of RelMon Service. This version uses CERN HTCondor to run `runTheMatrix.py` jobs.

## RelMon

One RelMon is one comparison job that can have multiple categories and multiple datasets to be compared. RelMon name should reflect what is being compared as this name will be used in reports page.

#### Categories
Categories in RelMon are the following: Data, FullSim, FastSim, Generator, FullSim PU, FastSim PU. All categories except Generator are treated the same. Generator has only "Only HLT" option. Categories are a convenient way to group comparisons in RelMon Service and reports pages. Each category has a list of references and targets.

#### References and targets
Items in references and targets lists are workflow names from ReqMgr2, e.g. `pdmvserv_RVCMSSW_11_0_0_..._190915_164000_1993`. Number of items must be equal in references and targets lists of the same category. If there are no references and targets in a category, it will be ignored.

#### Pairing
Items in references and targets lists can be paired either automatically or manually. Manual pairing compares first item in references list to first item in target list, second item to second item, etc. In this case it is up to a user to put them in correct order. In automatic pairing dataset names will be used to automatically make pairs based on run number (Data category only) and dataset name and processing string. Datasets with identical run numbers and datasets and most similar processing strings will be paired.

#### HLT
There are three options for HLT: No HLT, Only HLT and Both. This option controls `--HLT` flag of `ValidationMatrix.py`. "No HLT" will run `ValidationMatrix.py` only once for that category without `--HLT` flag. "Only HLT" will run only once for that category with the flag. "Both" will run `ValidationMatrix.py` twice for that category. Once with `--HLT` flag and then without it.

#### Other attributes
Each RelMon has few more attributes that could not be edited by a user.
  * **ID** - unique identifier, timestamp of RelMon creation
  * **Status** - RelMon status. It can be one of these:
    * `new` - RelMon is new and will soon be submitted to HTCondor for comparison
    * `submitted` - RelMon was successfully submitted to HTCondor and is waiting for resources to start running. Time in this status depends on RelMon size and load of HTCondor system
    * `running` - RelMon got resources in HTCondor and now is downloading files or running the `ValidationMatrix.py`. Time in this status depends on RelMon size
    * `finishing` - RelMon finished running all `ValidationMatrix.py` commands and now is packing and transferring reports to reports website
    * `done` - RelMon is done, reports are available
    * `failed` - RelMon submission or job at HTCondor failed. Carefully inspect workflow names, reset the RelMon or contact an administrator for more help
  * **HTCondor job status** - Status of HTCondor job. Usually it is one of these:
    * `IDLE` - job is waiting for resources
    * `RUN` - job is running
    * `DONE` - job is done
    * `<unknown>` - RelMon Service could not retrieve status of HTCondor job. This happens when HTCondor scheduler (manager) is not accessible. This is temporary and does not have influence on job. If job was running before, it will continue running, if it was IDLEing, it will continue doing that until resources are available
  * **HTCondor job ID** - job identifier in HTCondor. This is used mostly for debug purposes
  * **Last update** - when was the last time this RelMon received updates about itself like **Status*, **HTCondor job status** or **Progress**.
  * **Download progress** - how many DQMIO dataset files are downloaded
  * **Comparison progress** - rough estimate on `ValidationMatrix.py` progress based on number of categories and input file size
  * **Category status** - current status of this category. Can be one of these:
    * `initial` - category is waiting to be ran using `ValidationMatrix.py`
    * `comparing` - category is being compared at the moment
    * `done` - category is done being compared using `ValidationMatrix.py`
  * **References and targets status in categories** - status of each workflow and it's dataset. Can be one of these:
    * `initial` - workflow is waiting to have it's dataset downloaded
    * `downloading` - DQMIO dataset of this workflow is being currently downloaded
    * `downloaded` - DQMIO dataset of this workflow was successfully downloaded
    * `failed` - `.root` file exists, but error occurred while downloading the file. Contact administrator for more help
    * `no_workflow` - could not find workflow with given name in ReqMgr2
    * `no_dqmio` - workflow was found, but does not have DQMIO dataset among output datasets
    * `no_root` - workflow was found and has DQMIO dataset, but no corresponding `.root` file could be found in [https://cmsweb.cern.ch/dqm/relval/data/browse/ROOT/](https://cmsweb.cern.ch/dqm/relval/data/browse/ROOT/)

## How RelMon Service works

RelMon service works based on a loop. Each iteration of the loop performs these steps:
  1. RelMon Service checks in there are RelMons to be deleted. If there are, deletes them
  2. RelMon Service checks if there are RelMons to be reset. If there are, resets them
  3. RelMon Service checks if there are any jobs currently submitted to HTCondor. If there are, RelMon Service tries to get HTCondor job status by running `condor_q`
  4. RelMon Service checks if there are RelMons in status `new`. If there are, they are submitted to HTCondor
 
This loop automatically repeats every 10 minutes. Loop iteration is also triggered by creation of new RelMon, deletion, reset and edit actions, so user would not have to wait for 10 minutes to see the changes. It can also be triggered by clicking "Force Refresh" button. One iteration might take a couple of minutes if there are a bunch of RelMons that are submitted or need to be submitted.

## [For administrators] RelMon object structure in database

* id - unique identifier. Type: string, unix timestamp of RelMon creation time
* name - RelMon name. Type: string
* status - RelMon status in RelMon Service. Type: string
* last_update - timestamp of last update. Type: integer
* condor_status - last known status of HTCondor job. Type: string
* condor_id - last known HTCondor job id. Type: integer
* categories - list of categories that contain reference and target RelVals
```
{
  "id": <integer>,
  "name": <string>,
  "status": <string ["new", "submitting", "submitted", "running", "moving", "done", "failed", "terminating", "terminated", "resetting", "deleting"]>
  "last_update": <integer>,
  "condor_status": <string ["IDLE", "RUN", "DONE", "<unknown>"]>,
  "condor_id": <integer>,
  "categories": [
    {
      "name": <string ["Data", "Generator", "FullSim", "FullSim_PU", "FastSim", "FastSim_PU"]>,
      "HLT": <string ["no", "only", "both"]>,
      "status": <string ["initial", "comparing", "done"]>,
      "automatic_pairing": <boolean>,
      "reference": [
        {
          "name": <string>,
          "status": <string ["initial", "downloading", "downloaded", "failed", "no_workflow", "no_dqmio", "no_root"]>,
          "file_name": <string>,
          "file_size": <integer>,
          "file_url": <string>
        }
      ],
      "target": [
        {
          "name": <string>,
          "status": <string ["initial", "downloading", "downloaded", "failed", "no_workflow", "no_dqmio", "no_root"]>,
          "file_name": <string>,
          "file_size": <integer>,
          "file_url": <string>
        }
      ]
    }
  ]
}
```
