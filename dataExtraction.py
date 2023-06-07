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
from scipy.stats import norm

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
        if self.protocol == 'newwhiskerstim':
            self.sessionDate = self.matfileNameParts[2]
            self.sessionTime = self.matfileNameParts[3].split('.')[0]
        else:
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

        numberofTrials = self.data['nTrials'][0][0]
        reward = []
        for i in range(numberofTrials):
            # print(self.data['RawEvents']['Trial'][0][0][0][i]['States'][0][0]['Reward'][0][0][0])
            if np.any(np.isnan(self.data['RawEvents']['Trial'][0][0][0][i]['States'][0][0]['Reward'][0][0][0])):
                reward.append('No Reward')
            else:
                reward.append('Reward')

        tmp['Reward'] = pd.Series(reward)
        tmp['Go_noGo'] = np.where((tmp['TrialTypes'] == 1), 'Go', 'NoGo')

        tmp.loc[(tmp['Go_noGo'] == 'Go') & (tmp['Reward'] == 'Reward'), 'outcome']='Hit'
        tmp.loc[(tmp['Go_noGo'] == 'Go') & (tmp['Reward'] == 'No Reward'), 'outcome']='Miss'
        tmp.loc[(tmp['Go_noGo'] == 'NoGo') & (tmp['Reward'] == 'Reward'), 'outcome']='CR'
        tmp.loc[(tmp['Go_noGo'] == 'NoGo') & (tmp['Reward'] == 'No Reward'), 'outcome']='FA'
        tmp['sID'] = self.sID
        tmp['sessionDate'] = self.sessionDate
        tmp['sessionTime'] = self.sessionTime

        tmp = tmp.dropna(subset=['TrialStartTimestamp'])

        return tmp

    def getSessionInfoWisker_summary(self):
        dat = self.getSessionInfoWisker()
        dat = dat.groupby(['outcome']).agg({'trials': [np.ma.count]})#, 'frame': ['first']})
        datSum = dat.sum().item()
        dat = dat.T
        ## below a try except structure is necessary just in case some of the cases of configuration do not appear in a session
        for k in ['CR','FA','Hit','Miss']:
            try:
                dat[k+'_rate'] = dat[k].item()/datSum
            except:
                dat[k+'_rate'] = 0
                dat[k] = 0
        dat['Go'] = dat['Hit']+dat['Miss']
        dat['noGo'] = dat['CR']+dat['FA']
        dat['Go_rate'] = dat['Go']/datSum
        dat['total_correct'] = (dat['CR']+dat['Hit'])/datSum
        dat["d'"] =  norm.ppf(dat['Hit_rate'])- norm.ppf(dat['FA_rate'])
        dat['sID'] = self.sID
        dat['sessionDate'] = self.sessionDate
        dat['sessionTime'] = self.sessionTime
        dat['boxID'] = self.USBport
        dat['total_trials_n'] = dat['CR']+dat['FA']+dat['Hit']+dat['Miss']

        return dat

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
            ## TODO here the reward amount parsing for the wdil probably need to be worked out better 
            ## it works for the lickportraining but not for the 
            try:
                rewardAmount = pd.Series(self.data['TrialSettings'][0][j][0]['RewardAmount'][0][0][0][0])
            except:
                rewardAmount = pd.Series(np.nan)

            tmpTup =pd.DataFrame({'stateTime_on':pd.Series(self.data['RawEvents']['Trial'][0][0][0][j]['Events'][0][0]['Tup'][0][0][0][0]),
                                  'stateTime_off':pd.Series(self.data['RawEvents']['Trial'][0][0][0][j]['Events'][0][0]['Tup'][0][0][0][1]),
                                  'reward_amnt(ul)':rewardAmount})
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
        dat = pd.DataFrame({'sID':[self.sID], 
                            'protocol':[self.protocol], 
                            'sessionDate':[self.sessionDate], 
                            'sessionTime':[self.sessionTime], 
                            'boxID':[self.USBport],
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
            # print(i)
            ### the section below try/catch is to take care of the of no Port1Out which seems to happen in some cases
            eventsWdilParsed = self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0][0]
            if 'Port1In' not in eventsWdilParsed.dtype.names:
                myWdilPortIn = [np.nan]
            else:
                myWdilPortIn = eventsWdilParsed['Port1In'][0][0]
            if 'Port1Out' not in eventsWdilParsed.dtype.names:
                myWdilPortOut = [np.nan]
            else:
                myWdilPortOut = eventsWdilParsed['Port1Out'][0][0]

            try:
                if self.protocol == 'Licktraining':
                    licktime = pd.DataFrame({'stateTime':pd.Series(self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]['Port1In'][0][0][0]), 
                                             'LickOff':pd.Series(self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]['Port1Out'][0][0][0])})

                elif self.protocol == 'newwhiskerstim':


                    licktime = pd.DataFrame({'stateTime':pd.Series(myWdilPortIn), 
                             'LickOff':pd.Series(myWdilPortOut)}) #self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]

            except:
                if self.protocol == 'Licktraining':
                    licktime = pd.DataFrame({'stateTime':pd.Series(self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]['Port1In'][0][0][0]), 
                                             'LickOff':pd.Series(np.nan)})

                elif self.protocol == 'newwhiskerstim':
                    licktime = pd.DataFrame({'stateTime':pd.Series(myWdilPortIn), 
                             'LickOff':pd.Series(myWdilPortOut)}) #self.data['RawEvents']['Trial'][0][0][0][i]['Events'][0][0]

            
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
        res['sessionTime'] = self.sessionTime
        res.loc[res['lickDuration_max']<0,'strangeState']=1
        res.loc[res['lickDuration_max'].isna(),'strangeStateNaN']=1

        return res




    def getTheState(self):
        def intervalCount(df, lower_bound, upper_bound):
            count = df[(df['stateTime'] >= lower_bound) & (df['stateTime'] <= upper_bound)].shape[0]
            meanDuration = df.loc[(df['stateTime'] >= lower_bound) & (df['stateTime'] <= upper_bound),'lickDuration'].mean()
            return count, meanDuration

        # get the code of the sate based on the matrix
        # trialN = 3
        allLicksout = self.getLicks()
        tmpB = self.getSessionInfoWisker()
        # the 'ResponseState is actually the reaction time' 
        licks_allTrials = []
        reactionTime_allTrials = []
        for trialN in range(len(tmpB)):
            stateName = self.data['RawData']['OriginalStateNamesByNumber'][0][0][0][trialN][0]
            stateName = [item[0] for item in stateName.tolist()]
            stateCodeTable = pd.DataFrame({'stateCode':np.array(range(len(stateName)))+1,'stateName':stateName})

            # get the state timing
            stateTiming = pd.DataFrame({
                'stateCode':self.data['RawData']['OriginalStateData'][0][0][0][trialN][0],
                'stateTime':self.data['RawData']['OriginalStateTimestamps'][0][0][0][trialN][0][1:]
            })
            stateTiming = pd.merge(stateCodeTable, stateTiming, on='stateCode', how='outer')
            stateTiming = stateTiming.dropna()

            ## construction of the grouping table
            ## variables of the tables

            v_start = stateTiming.loc[stateTiming['stateName']=='StartState','stateTime'].max()
            v_stim = stateTiming.loc[stateTiming['stateName']=='StimState','stateTime'].max()
            v_Resp = stateTiming.loc[stateTiming['stateName']=='ResponseState','stateTime'].max()
            v_Reward = stateTiming.loc[stateTiming['stateName']=='Reward','stateTime'].max()
            v_Error = stateTiming.loc[stateTiming['stateName']=='Error','stateTime'].max()
            v_drinking = stateTiming.loc[stateTiming['stateName']=='DrinkingTime','stateTime'].max()
            v_iti = stateTiming.loc[stateTiming['stateName']=='ITI','stateTime'].max()
            
            if v_Reward is not np.nan:
                classification = 'Reward'
                stateTimeStart = [0, v_start, v_Resp, v_Reward, v_drinking]
                stateTimeStop = [v_start, v_stim, v_Reward, v_drinking, v_iti]
            elif v_Error is not np.nan:
                classification = 'Error'
                stateTimeStart = [0, v_start, v_Resp, v_Error, v_drinking]
                stateTimeStop = [v_start, v_stim, v_Error, v_drinking, v_iti]

            stateCluster = ['preTone','ToneStim','postResponse','drinking','postDrinking']
            stateTimeStart = [0, v_start, v_Resp, v_Reward, v_drinking]
            stateTimeStop = [v_start, v_stim, v_Reward, v_drinking, v_iti]

            licks_singleTrial = []
            for kdx, k in enumerate(zip(stateCluster,stateTimeStart,stateTimeStop)):
                # print(kdx,k)
                tmpallLicksout = allLicksout[allLicksout['trials']==trialN]
                tmpCnt, meanDur = intervalCount(tmpallLicksout, k[1], k[2])
                # print(tmpCnt)
                lickCountTable = pd.DataFrame({
                    'licks(n)':pd.Series(tmpCnt),
                    'licks(meanDur)':pd.Series(meanDur),
                    'Interval_cat':pd.Series(k[0]),
                    'Interval_start':pd.Series(k[1]),
                    'Interval_stop':pd.Series(k[2])
                    })
                lickCountTable['trials'] = trialN
                licks_singleTrial.append(lickCountTable)

            licks_singleTrial = pd.concat(licks_singleTrial)
            licks_singleTrial['type'] = classification
            licks_allTrials.append(licks_singleTrial)

            ### Get the reaction time
            reactionTime = pd.DataFrame({
                'reactionTime':stateTiming.loc[stateTiming['stateName']=='ResponseState','stateTime'],
                'trials':[trialN]})
            reactionTime_allTrials.append(reactionTime)

        reactionTime_allTrials = pd.concat(reactionTime_allTrials)
        licks_allTrials = pd.concat(licks_allTrials)




        return licks_allTrials, reactionTime_allTrials

        ### pieces of code to test and check the timing
        #     stateTimingReRe = stateTiming.loc[stateTiming['stateName']=='ResponseState','stateTime'].item()-stateTiming.loc[stateTiming['stateName']=='Error','stateTime'].item()
        #     allL.append(stateTimingReRe)

        # tmpB['timingTest'] = allL

        # plt.figure()
        # for i,j in zip(['CR', 'FA', 'Hit', 'Miss'],['black','blue','green','orange']):
        #     print(i,j)
        #     plt.plot(tmpB.loc[tmpB['outcome']==i,'timingTest'],'.',color=j,label=i)
        # plt.legend()



    ## need to get the reaction out of the 


    def getLicksTrials_summary(self):
        ## data for number of licks 
        tmpA = self.getSessionInfoWisker()[['trials','outcome']]
        tmpB = pd.merge(tmpA, self.getLicks_summary(), on='trials')
        tmpB_summary = tmpB.groupby(['outcome']).agg({'licks(n)': [np.mean, np.sum, np.min, np.max]})

        ## data for reaction based on outcome
        licks_allTrials, reactionTime = self.getTheState()
        reactionTime = pd.merge(reactionTime, tmpA, on='trials')
        reactionTime_summary = reactionTime.groupby(['outcome']).agg({'reactionTime': [np.mean, np.min, np.max]})


        combined = pd.concat([tmpB_summary, reactionTime_summary], axis=1)
        combined['sID'] = self.sID
        combined['sessionDate'] = self.sessionDate
        combined['sessionTime'] = self.sessionTime


        ## data for reaction based on outcome
        licks_allTrials = pd.merge(licks_allTrials, tmpA, on='trials')
        licks_allTrials_summary = licks_allTrials.groupby(['outcome','Interval_cat']).agg({'licks(n)': [np.mean, np.min, np.max], 'licks(meanDur)': [np.mean, np.min, np.max]})
        licks_allTrials_summary['sID'] = self.sID
        licks_allTrials_summary['sessionDate'] = self.sessionDate
        licks_allTrials_summary['sessionTime'] = self.sessionTime

        return combined, licks_allTrials_summary


# isolate and get only the lickport training data

tmpFol = r'Y:\Vaissiere\New folder'
## run accross all the folder 
## TODO should discriminate for the file in the class between lick port analysis or wdil

def lickportAnalysis():
    matFiles = list(set(glob.glob(tmpFol+'/**/*Licktraining_bpod*.mat', recursive=True))-set(glob.glob(tmpFol+'/**/*DefaultSettings.mat', recursive=True)))

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
    allLickSummary.to_csv(exportFolder+os.sep+'allLickSummary_lickport.csv')
    allDatSummary.to_csv(exportFolder+os.sep+'globalSummary_lickport.csv')

    print('Outputs are located here:')
    print(exportFolder+'allLickSummary.csv')
    print(exportFolder+'globalSummary.csv')

def lickWDILAnalysis():
    tmpFol =  r'Y:\Vaissiere\New folder'##<<------- to be deleted
    matFiles = list(set(glob.glob(tmpFol+'/**/*newwhiskerstim*.mat', recursive=True))-set(glob.glob(tmpFol+'/**/*DefaultSettings.mat', recursive=True)))

    wdil_perf_trials_ALL = []
    wdil_perf_summary_ALL = []
    licks_allTrials_ALL = []
    licks_reactionTime_summary_ALL =  []
    licks_allTrials_summary_ALL = []
    for i in tqdm.tqdm(matFiles):
        print(i)
        try:
            a = matExtraction(i)
            #get all the wdil data
            wdil_perf_trials = a.getSessionInfoWisker() # full trial information
            wdil_perf_trials_simplify = wdil_perf_trials[['trials','outcome']]

            wdil_perf_summary = a.getSessionInfoWisker_summary() # one line summary of wdil performance
            lick_summary = a.getSessionInfoLickTrain_summary()
            wdil_perf_summary = wdil_perf_summary
            lick_summary = lick_summary
            wdil_perf_summary = pd.merge(wdil_perf_summary, lick_summary, on=['sID','sessionDate','sessionTime','boxID'])
            wdil_perf_summary['sID'] = a.sID
            wdil_perf_summary['sessionDate'] = a.sessionDate
            wdil_perf_summary['sessionTime'] = a.sessionTime


            ## lick per trials
            # lick_trials = a.getLicks_summary() not necessary to have this output 
 
            licks_allTrials, reactionTime = a.getTheState()
            licks_allTrials = pd.merge(wdil_perf_trials_simplify, licks_allTrials, on = 'trials')
            licks_allTrials['sID'] = a.sID
            licks_allTrials['sessionDate'] = a.sessionDate
            licks_allTrials['sessionTime'] = a.sessionTime


            licks_reactionTime_summary, licks_allTrials_summary = a.getLicksTrials_summary()

            ## appending sections 
            ###--------------------------------------------------------------------------
            '''
            to output
            `wdil_perf_trials`: detail output of the status of go/nogo, reward etc for the session
            `wdil_perf_summary`: overall statistic on the trial 
            `licks_allTrials`: data for which all the licks pere trial category are recorded
            `licks_reactionTime_summary`: summary of reaction and licks 
            `licks_allTrials_summary`: summary of licks by session timing 
            '''

            wdil_perf_trials_ALL.append(wdil_perf_trials)
            wdil_perf_summary_ALL.append(wdil_perf_summary)
            licks_allTrials_ALL.append(licks_allTrials)
            licks_reactionTime_summary_ALL.append(licks_reactionTime_summary)
            licks_allTrials_summary_ALL.append(licks_allTrials_summary)

        except:
            print(f'------------------------------------------------------------')
            print(f'-- ERROR ERROR with \n {i}')
            print(f'------------------------------------------------------------')

    dataOut = {'wdil_goNoGo_status': wdil_perf_trials_ALL, 
               'wdil_sessionStat': wdil_perf_summary_ALL, 
               'wdil_all_Licks': licks_allTrials_ALL, 
               'wdil_reactionTime': licks_reactionTime_summary_ALL, 
               'wdil_Licks_byCat': licks_allTrials_summary_ALL}
    
    for k in dataOut:
        try:
            tmp = pd.concat(dataOut[k])
            tmp = tmp.sort_values(by=['sID','sessionDate','sessionTime'])
            exportFolder = tmpFol+os.sep+'Analysis'+os.sep+'WDIL_data'
            os.makedirs(exportFolder,exist_ok=True)
            tmp.to_csv(exportFolder+os.sep+k+'.csv')
        except:
            print('no')


if analysisType == str(1):
    lickportAnalysis()
elif analysisType == str(2):
    lickWDILAnalysis()
elif analysisType == str(3):
    lickWDILAnalysis()
    lickportAnalysis()
