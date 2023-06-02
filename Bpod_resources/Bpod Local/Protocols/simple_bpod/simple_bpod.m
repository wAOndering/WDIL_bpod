function simple_bpod
%2023

%% Load Bpod variables and start USB connections to any modules
global BpodSystem

%% Setup (runs once before the first trial
%--- Define parameters and trial structure

S = BpodSystem.ProtocolSettings; % Loads settings file chosen in launch manager into current workspace as a struct called 'S'
if isempty(fieldnames(S))  % If chosen settings file was an empty struct, populate struct with default settings
    % Define default settings here as fields of S (i.e S.InitialDelay = 3.2)
    % Note: Any parameters in S.GUI will be shown in UI edit boxes.
    % See ParameterGUI plugin documentation to show parameters as other UI types (listboxes, checkboxes, buttons, text)
    S.GUI.RewardAmount = 4; %ul---only to try the gui
end

%--- Initialize panels
BpodParameterGUI('init', S); % Initialize parameter GUI plugin
% TotalRewardDisplay('init'); %initialize the water consumption tracker
%BpodNotebook('init'); % Launches an interface to write notes about

%% Define trials
MaxTrials = 5000; % Set to some sane value, for preallocation
rng('shuffle')   % Reset pseudorandom seed
TrialTypes = zeros(1,MaxTrials)+1; % if you only have one lickport, add the ID number of the port



BpodSystem.Data.TrialTypes = TrialTypes; % we save here the predefined trialtype

%% Main loop (runs once per trial)
for currentTrial = 1:MaxTrials
    S = BpodParameterGUI('sync', S); % Sync parameters with BpodParameterGUI plugin
    %BpodSystem.Data = BpodNotebook('sync', BpodSystem.Data); %not sure of the place of this
    
    %Defined actions (in sma)
    Output = {'Flex1AO', 2};
    WhiskStimDelivery = {'BNC2', 1}

        sma = NewStateMatrix();
        sma = AddState(sma,'Name', 'Wait', ... %it will deliver anyway, even if the animal doesn't lick
            'Timer', 2,...
            'StateChangeConditions', {'Tup', 'LED'},...
            'OutputActions', {});
        sma = AddState(sma,'Name', 'LED', ...
            'Timer',3,...
            'StateChangeConditions', {'Tup', 'Timeout'},...
            'OutputActions', [WhiskStimDelivery Output]);
        sma = AddState(sma,'Name','Timeout',...   %or the animal has to withhold their licking?
            'Timer',5,...
            'StateChangeConditions',{'Tup','exit'},...
            'OutputActions',{});
        
        SendStateMatrix(sma); % Send state machine to the Bpod state machine device
        RawEvents = RunStateMatrix; % Run the trial and return events
        
        %--- Package and save the trial's data, update plots
        if ~isempty(fieldnames(RawEvents)) % If you didn't stop the session manually mid-trial
            BpodSystem.Data = AddTrialEvents(BpodSystem.Data,RawEvents); % Adds raw events to a human-readable data struct
            BpodSystem.Data.TrialSettings(currentTrial) = S; % Adds the settings used for the current trial to the Data struct (to be saved after the trial ends)
            SaveBpodSessionData; % Saves the field BpodSystem.Data to the current data file
            
        end
        %--- This final block of code is necessary for the Bpod console's pause and stop buttons to work
        HandlePauseCondition; % Checks to see if the protocol is paused. If so, waits until user resumes.
        if BpodSystem.Status.BeingUsed == 0
            return
        end
end
end



