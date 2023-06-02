####################################
## FUNCTIONS
####################################
import warnings
warnings.simplefilter("ignore")
import pandas as  pd
import glob
import os
import scipy.io
import logging
import matplotlib.pyplot as plt
import numpy as np
import re
import glob
import ctypes
import logging
import tqdm

# ctypes.windll.kernel32.SetConsoleTitleW("py310")




### to be used in command prompt
print('')
print('-------------------------------------------')
tmpFol = input("Drag the parent folder/directory with all the WDIL data example and press Enter:")
tmpFol = tmpFol.replace('\\','/')
tmpFol = tmpFol.replace('"','')
print('-------------------------------------------')
print('')

## create an analysis folder
os.makedirs(tmpFol+os.sep+'Analysis', exist_ok=True)

## select analysis option
print('')
print('-------------------------------------------')
print('Select the type of analysis:')
print("1: lickport training")
print("2: wdil data")
print("3: lickport training and wdil data")
analysisType = input('make a selection (1,2 or 3):')
print('-------------------------------------------')
print('')


# logging.basicConfig(filename=r'C:\Users\Windows\Desktop\error.log', level=logging.ERROR,
#                     format='%(asctime)s %(levelname)s: %(message)s')

logging.basicConfig(filename=tmpFol+os.sep+'error.log', filemode='w', level=logging.INFO)

def quickConversion(tmp, myCol=None, option=2):
    ''' convert groupby pandas table into a simpler version
    '''
    if option ==1:
        tmp.columns = ['value']
        tmp = tmp.reset_index()
        if tmp.columns.nlevels > 1:
            tmp.columns = ['_'.join(col) for col in tmp.columns] 
        tmp.columns = tmp.columns.str.replace('[_]','')
        if myCol:
            tmp = tmp.rename(columns={np.nan: myCol})
        return tmp
    elif option ==2:
        tmp.columns = ['_'.join(col) for col in tmp.columns] 
        tmp = tmp.reset_index()
        return tmp

class matExtraction:
    '''
    #TODO: replace the following code and placed them in the initial part
            mat = scipy.io.loadmat(self.filename_mat)
            a = mat['SessionData'][0][0]
            then replace a by self.a or a better containing variable 


    #### Example test individual function within the class
    # a = matExtraction(matFiles[0])
    # # a.getSessionInfoWisker()
    # a.getSessionInfoLickTrain()
    # a.getSessionInfoLickTrain_summary()
    # a.getLicks()
    # a.getLicks_summary()

    '''

    def __init__(self, matfileName):
        ''' to check 

        '''
        self.filename_mat = matfileName
        self.matfileNameParts = os.path.basename(matfileName).split('_')
        self.sID = self.matfileNameParts[0]
        self.protocol = self.matfileNameParts[1]
        self.sessionDate = self.matfileNameParts[3]
        self.sessionTime = self.matfileNameParts[4].split('.')[0]
        self.data = scipy.io.loadmat(self.filename_mat)['SessionData'][0][0]
        self.USBport = self.data['Info']['Modules'][0][0]['USBport'][0][0][0][0][0]
        # print(self.sID, self.protocol, self.sessionDate, self.sessionTime)

    def getSessionInfoWisker(self):
        ## print some of the values 
            ## print(mat.keys(), mat.items(), mat.values())
            # a = mat[0][0]
            # colLabel = a.dtype.names

            # for i in a.dtype.names:
            #   print(a[i])
        tmp = pd.DataFrame()

        for i in ['TrialType50','TrialType0','TrialType100','TrialTypes','TrialStartTimestamp','TrialEndTimestamp','ITITypes']:
            tmp[i] = pd.Series(self.data[i][0]) #pd.Series will fill with NA

        tmp['trialDuration'] = tmp['TrialEndTimestamp']-tmp['TrialStartTimestamp']
        tmp['trials'] = tmp.index

        return tmp

    def getSessionInfoLickTrain(self):
        ''' 
        This is the trial session information

        in this case the trial session is when it starts and stop. The useful infomration would be to get a summary
        of that trial session 

        '''
        ## get
        tmp = pd.DataFrame()
        for i in ['TrialStartTimestamp','TrialTypes','TrialEndTimestamp']:
            tmp[i] = pd.Series(self.data[i][0]) #pd.Series will fill with NA
        tmp['trialDuration'] = tmp['TrialEndTimestamp']-tmp['TrialStartTimestamp']
        tmp['trials'] = tmp.index

        ## get the value for Tup for all the trials in a session
        ## this value 
        TupRawEvent = []
        for j in range(len(tmp)):
            tmpTup =pd.DataFrame({'stateTime_on':pd.Series(self.data['RawEvents']['Trial'][0][0][0][j]['Events'][0][0]['Tup'][0][0][0][0]),
                                  'stateTime_off':pd.Series(self.data['RawEvents']['Trial'][0][0][0][j]['Events'][0][0]['Tup'][0][0][0][1]),
                                  'reward_amnt(ul)':self.data['TrialSettings'][0][j][0]['RewardAmount'][0][0][0][0]})
            tmpTup['trials'] = j
            TupRawEvent.append(tmpTup)
        TupRawEvent=pd.concat(TupRawEvent)

        tmp = pd.merge(tmp, TupRawEvent, on='trials')

        return tmp

    def getSessionInfoLickTrain_summary(self):
        '''
        to get the summary of the function

        this can may be generalized regardless of training and testing
        '''
        ## general set up for the info about the session
        ## add on o fthe summary with some state regarding the licks
        lickDat = self.getLicks_summary()

        dat = self.getSessionInfoLickTrain()
        dat = pd.DataFrame({'sID':[self.sID], 'protocol':[self.protocol], 'sessionDate':[self.sessionDate],
                            'nTrials':[len(dat)], 'avgTrialDur(s)':np.average(dat.trialDuration),
                            'maxTrialDur(s)':np.max(dat.trialDuration),
                            'minTrialDur(s)':np.min(dat.trialDuration),
                            'reward_amnt(ul)':np.average(dat['reward_amnt(ul)']),
                            ### this section below incorportate some stat about the licks 
                            'licks_all(n)':[lickDat['licks(n)'].sum()],
                            'licks_avg_per_trials(n)':[lickDat['licks(n)'].mean()],
                            'licks_min(n)_withinTrial':[lickDat['licks(n)'].min()],
                            'licks_max(n)_withinTrial':[lickDat['licks(n)'].max()],
                            'licks_abnormalState (ratio)':[lickDat['strangeState'].sum()/len(lickDat)],
                            'licks_abnormalState (n)':[lickDat['strangeState'].sum()],
                            'licks_abnormalStateNaN (ratio)':[lickDat['strangeStateNaN'].sum()/len(lickDat)],
                            'licks_abnormalStateNaN (n)':[lickDat['strangeStateNaN'].sum()]})

        return dat

    def getLicks(self):
        if self.protocol == 'newwhiskerstim':
            sessionInfo = self.getSessionInfoWisker()
        elif self.protocol == 'Licktraining':
            sessionInfo = self.getSessionInfoLickTrain()

        all_licks = []
        TupRawEvent = []
        for i in sessionInfo['trials']:
            ### the section below try/catch is to take care of the of no Port1Out which seems to happen in some cases
            try:
                licktime = pd.DataFrame({'stateTime':pd.Series(self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]['Port1In'][0][0][0]), 'LickOff':pd.Series(self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]['Port1Out'][0][0][0])}) ## need to switch a to self.data
            except:
                licktime = pd.DataFrame({'stateTime':pd.Series(self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]['Port1In'][0][0][0]), 'LickOff':pd.Series(np.nan)})
            
            licktime['trials'] = i
            all_licks.append(licktime)

        all_licks = pd.concat(all_licks)
        all_licks['lickDuration'] = all_licks['LickOff'] - all_licks['stateTime']

        return all_licks

    def getLicks_summary(self):
        tmp = self.getLicks()
        res = tmp.groupby(['trials']).agg({'trials': [np.ma.count], 'lickDuration': [np.mean, min, max]})#, 'frame': ['first']})
        res = quickConversion(res)
        res = res.rename(columns={'trials_count':'licks(n)'})
        res['strangeState'] = 0
        res['strangeStateNaN'] = 0
        res.loc[res['lickDuration_max']<0,'strangeState']=1
        res['sID'] = self.sID
        res['sessionDate'] = self.sessionDate
        res.loc[res['lickDuration_max']<0,'strangeState']=1
        res.loc[res['lickDuration_max'].isna(),'strangeStateNaN']=1

        return res


# isolate and get only the lickport training data
matFiles = list(set(glob.glob(tmpFol+'/**/*.mat', recursive=True))-set(glob.glob(tmpFol+'/**/*DefaultSettings.mat', recursive=True)))


## run accross all the folder 
## TODO should discriminate for the file in the class between lick port analysis or wdil

def lickportAnalysis():
    allDatSummary = []
    allLickSummary = []
    for i in tqdm.tqdm(matFiles):
        print(i)
        a = matExtraction(i)
        tmp = a.getSessionInfoLickTrain_summary()
        tmpt = a.getLicks_summary()
        # print(f'bad: {a.sID, a.USBport}')
        allDatSummary.append(tmp)
        allLickSummary.append(tmpt)
    allDatSummary = pd.concat(allDatSummary)
    allLickSummary = pd.concat(allLickSummary)

    allDatSummary = allDatSummary.sort_values(by=['sID','sessionDate'])
    allLickSummary = allLickSummary.sort_values(by=['sID','sessionDate'])

    exportFolder = tmpFol+os.sep+'Analysis'+os.sep+'Lickport_data'
    os.makedirs(exportFolder,exist_ok=True)
    allLickSummary.to_csv(exportFolder+os.sep+'allLickSummary.csv')
    allDatSummary.to_csv(exportFolder+os.sep+'globalSummary.csv')

    print('Outputs are located here:')
    print(exportFolder+'allLickSummary.csv')
    print(exportFolder+'globalSummary.csv')

def lickWDILAnalysis():
    exportFolder = tmpFol+os.sep+'Analysis'+os.sep+'WDIL_data'
    os.makedirs(exportFolder,exist_ok=True)

if analysisType == str(1):
    lickportAnalysis()
elif analysisType == str(2):
    lickWDILAnalysis()
elif analysisType == str(3):
    lickWDILAnalysis()
    lickportAnalysis()