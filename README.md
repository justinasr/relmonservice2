# relmonservice2
RelmonService2

### Relmon structure

Each RelMon is a is an object. RelMon structure:

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