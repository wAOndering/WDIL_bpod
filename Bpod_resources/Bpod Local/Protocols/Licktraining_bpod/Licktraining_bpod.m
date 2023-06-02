function Licktraining_bpod
%   LICKTRAINING_BPOD protocol based the protocol from Rumbaugh lab
%   lickport training before sensory stimulation (senslick2)
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
    S.GUI.RewardAmount = 8; %ul
    S.GUI.ITILickTime = 1.25; %s; or 1.5; ITI between liquid deliveries
    S.GUI.TrialLength = 600; %s; max time of the session
    S.GUI.MaxWater = 1000; % probably it is in ul
end

%--- Initialize panels
BpodParameterGUI('init', S); % Initialize parameter GUI plugin
TotalRewardDisplay('init'); %initialize the water consumption tracker
%BpodNotebook('init'); % Launches an interface to write notes about

%% Define trials
MaxTrials = 5000; % Set to some sane value, for preallocation
rng('shuffle')   % Reset pseudorandom seed
TrialTypes = zeros(1,MaxTrials)+1; % if you only have one lickport, add the ID number of the port

BpodSystem.Data.TrialTypes = TrialTypes; % we save here the predefined trialtype

%% Main loop (runs once per trial)
tic % this is to get the general time before the loop
for currentTrial = 1:MaxTrials 
    S = BpodParameterGUI('sync', S); % Sync parameters with BpodParameterGUI plugin
    %BpodSystem.Data = BpodNotebook('sync', BpodSystem.Data); %not sure of the place of this
    V = GetValveTimes(S.GUI.RewardAmount, [1]);   % Update reward amounts
    RewardValveTime = V(1);
    
    %Defined actions (in sma)
    RewardDelivery = {'ValveState', 1};
    
    
    if currentTrial>1
        licktime = BpodSystem.Data.TrialStartTimestamp(1,currentTrial-1); %get elapsed time from previous trial (current one hasn't saved yet)
        water = S.GUI.RewardAmount * (currentTrial-1); %get the amount of water consumed--this is the delivered! amout
        %probably easier to get from the water consumption panel, but we have
        %to test it
    else
        licktime = 0; %first trial
        water = 0;
    end
    
    if toc>S.GUI.TrialLength % this is done to take care of the timing due to the strange behavior of the OR in the next if statement
        display('Session is ended because 10 min is up')
        break
    end    
    if water < S.GUI.MaxWater % we have to test it, sometimes OR works funny here
         display(toc)
%         display(timeSinceSessionStart)
%         display(licktime)
%         display(water)
        sma = NewStateMatrix();
        sma = AddState(sma,'Name', 'WaitforLick', ... %it will deliver anyway, even if the animal doesn't lick
            'Timer', 0,...    %I think it should be zero, but have to test it
            'StateChangeConditions', {'Port1In','Reward'},...
            'OutputActions', {});
        sma = AddState(sma,'Name', 'Reward', ...
            'Timer',RewardValveTime,...
            'StateChangeConditions', {'Tup', 'Timeout'},...
            'OutputActions', RewardDelivery);
        sma = AddState(sma,'Name','Timeout',...   %or the animal has to withhold their licking?
            'Timer',S.GUI.ITILickTime,...
            'StateChangeConditions',{'Tup','exit'},...
            'OutputActions',{});
        
        SendStateMatrix(sma); % Send state machine to the Bpod state machine device
        RawEvents = RunStateMatrix; % Run the trial and return events
        
        %--- Package and save the trial's data, update plots
        if ~isempty(fieldnames(RawEvents)) % If you didn't stop the session manually mid-trial
            BpodSystem.Data = AddTrialEvents(BpodSystem.Data,RawEvents); % Adds raw events to a human-readable data struct
            BpodSystem.Data.TrialSettings(currentTrial) = S; % Adds the settings used for the current trial to the Data struct (to be saved after the trial ends)

            UpdateTotalRewardDisplay(S.GUI.RewardAmount, currentTrial); %calculate the water consumption
            SaveBpodSessionData; % Saves the field BpodSystem.Data to the current data file
            
        end
        %--- This final block of code is necessary for the Bpod console's pause and stop buttons to work
        HandlePauseCondition; % Checks to see if the protocol is paused. If so, waits until user resumes.
        if BpodSystem.Status.BeingUsed == 0
            return
        end
        
    else
        display('Session is ended because amount of water was reached')
        %             s = serial('COM3');
        %             fclose(s); prbably we don't have to close, but have
        %             to test
        break %break the loop based on elapsed time and water amount
    end
end
end
% -------------------------------------------------------------------------
%--- Typically a block of code here will update online plots using the newly updated BpodSystem.Data

%Update reward amount
function UpdateTotalRewardDisplay(RewardAmount, currentTrial)
% If rewarded based on the state data, update the TotalRewardDisplay
global BpodSystem
if ~isnan(BpodSystem.Data.RawEvents.Trial{currentTrial}.States.Reward(1))
    TotalRewardDisplay('add', RewardAmount);
end
end

