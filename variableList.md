#####################################################################
####################### VARIALBES ###################################

('TrialType50', # review ok need clarification on 1 and 2
 'TrialType0', # review ok need clarification on 1 and 2
 'TrialType100', # review ok need clarification on 1 and 2
 'TrialType', # empty 
 'ITITypes', # ok need clarification on representation of integer value looks like this correspond to the integer value of time 
 'Info', ## another structure not necessary to deal with
 'nTrials',## number of trials before session end
 'RawEvents', ## this is a structure >>>>>>>>>>>> Need to setup trials with reward and early detect
 		('Trial')
 			('States',
 				('')
 			 'Events')
 				('Port1In',
 				 'Tup',
 				 'Port1Out',
 				 'HiFi1_1')

 'RawData',
		('OriginalStateNamesByNumber', # redundant across trial definition of the State
		 'OriginalStateData', # actual State which occured during trial
		 'OriginalEventData', # ???? number 154 1 88 89 not sure what they coorespond to
		 'OriginalStateTimestamps', # timing of the state transition
		 'OriginalEventTimestamps', # event data and event Timestamps
		 'StateMachineErrorCodes')
 'TrialStartTimestamp', # ok 
 'TrialEndTimestamp', # ok
 'SettingsFile', #empty
 'TrialSettings', # actual 
 'TrialTypes',
 'Notes',
 'MarkerCodes')