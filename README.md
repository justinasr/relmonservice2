# relmonservice2
RelmonService2

### Relmon structure

Each RelMon is a dictionary (JSON) file. Structure:
```
{
    "id": <integer>,
    "name": <string>,
    "status": <string ["new", "submitting", "submitted", "running", "finishing", "done", "failed"]>
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