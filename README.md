# WDIL_bpod

Update from https://github.com/wAOndering/WDIL_lick.git. This repository contains Bpod protocol to run the Whisker Dependent Instrumental Learning task (WDIL) with the Bpod Gen2 protocol. 
It also contains python scripts to extract data from the Matlab files:
* to get analysis of the lick behavior during the lickport 
* to get analysis of the lick behavior during WDIL data acquisition
* to get information about the data. 

## Resources:
* This folder contains the portocol used with bpod [protocols](https://github.com/wAOndering/WDIL_bpod/tree/main/Bpod_resources/Bpod%20Local/Protocols)
* `WDIL protocol` Adapted by Diana Balazsfi is the following protocol for WDIL with bpod [wdil_protocol](https://github.com/wAOndering/WDIL_bpod/blob/main/Bpod_resources/Bpod%20Local/Protocols/newwhiskerstim/newwhiskerstim.m)

* `Lickport protocol` Adapted by Diana Balazsfi is the following protocol forlick port training only with bpod [lick_protocol](https://github.com/wAOndering/WDIL_bpod/blob/main/Bpod_resources/Bpod%20Local/Protocols/Licktraining_bpod/Licktraining_bpod.m)

* List of variables and structure within .mat file output https://github.com/wAOndering/WDIL_bpod/blob/main/variableList.md

* See the original code repo for the bpod system [here](https://github.com/sanworks/Bpod_Gen2)
## Usage:
### instruction
*  install [Anaconda](https://www.anaconda.com/)
*  Start Anaconda command prompt
*  In the command prompt type: `python `
*  Drag and drop the file `dataExtraction.py` in the command prompt or enter the file path (eg. "C:\git\WDIL_bpod\dataExtraction.py") then press `Enter`
*  Follow the instructions<!-- add `space` before drag and drop the **Folder** containing the files of interest -->
*  press `Enter`

## Outputs:
### data files:
#### lickport Trainnig
* `combinedOutput.csv`: contains normalized and raw values from nanoluc and ffluc plates in a long format with wellPosition
* `normPlate_norm_ffluc.csv`: is a matrix of the plate normalized to DMSO control for ffluc in a plate format (useful for heatmap
* `normPlate_norm_nanoluc.csv`: is a matrix of the plate normalized to DMSO control for nanoluc in a plate format (useful for heatmap)
* `outerSample.csv`: is a list of all the samples that fall outside of the threshold (3SD DMSO control)
* `Samples_stats.csv`: stats with CV, mean, SD, counts pers sample for raw and norm value of ffluc and nanoluc

#### wdil Trainnig
* `wdil_perf_trials`: detail output of the status of go/nogo, reward etc for the session
* `wdil_perf_summary`: overall statistic on the trial 
* `licks_allTrials`: data for which all the licks pere trial category are recorded
* `licks_reactionTime_summary`: summary of reaction and licks 
* `licks_allTrials_summary`: summary of licks by session timing 

## Notes 
- Need to setup a conda environment and actual package with dependencies. Currently this will work just fine on proper install. If it fails it might probably be due to lacking libraries.
- can adapt it to have virtual env as well 