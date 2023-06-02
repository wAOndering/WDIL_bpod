function WhiskerStim_bpod
%   WHISKERSTIM_BPOD protocol based on the original WhiskerStim for bcontrol
%   and github protocols: cued outcome task and ATS from:
%   https://github.com/hangyabalazs
%   and protocol from Rumbaugh lab for sensory stimulation (sensw2)
%2023
%% SETUP
% You will need:
% - A Bpod state machine v0.7+
% - A Bpod HiFi module, loaded with BpodHiFiPlayer firmware.
% - Connect the HiFi module's State Machine port to the Bpod state machine
% - From the Bpod console, pair the HiFi module with its USB serial port.
% - Connect channel 1 (or ch1+2) of the hifi module to an amplified speaker(s).

%% Load Bpod variables and start USB connections to any modules
global BpodSystem

% Assert HiFi module is present + USB-paired (via USB button on console GUI)
BpodSystem.assertModule('HiFi', 1); % The second argument (1) indicates that the HiFi module must be paired with its USB serial port-sayingYES
% Create an instance of the HiFi module
H = BpodHiFi(BpodSystem.ModuleUSB.HiFi1); % The argument is the name of the HiFi module's USB serial port (e.g. COM3)-hopefully finds itself
% H = BpodHiFi('COM3'); % if it cannot find by itself
%% Setup (runs once before the first trial
%--- Define parameters and trial structure
%Setup (runs once before the first trial)

S = BpodSystem.ProtocolSettings; % Loads settings file chosen in launch manager into current workspace as a struct called 'S'
if isempty(fieldnames(S))  % If chosen settings file was an empty struct, populate struct with default settings
    % Define default settings here as fields of S (i.e S.InitialDelay = 3.2)
    %it doesn't appear in the GUI
    S.StartState = 1.5; % s, time animal has to withold licking
    S.SoundDuration = 0.25; % s
    S.SinWaveFreq = 7000; %Hz
    S.WhiskerStim = 0.1; % s
    S.ResponseTime = 2;
    S.DrinkingTime = 2;
    %     S.ITI = 4; %if you'd like to have a fixed time
    % Note: Any parameters in S.GUI will be shown in UI edit boxes.
    % See ParameterGUI plugin documentation to show parameters as other UI types (listboxes, checkboxes, buttons, text)
    S.GUI.RewardAmount = 7; %ul
    
    S.GUI.Type1 = 0.5; %Probability of trial type 1/GO trial (e.g.: 1GO,2NOGO,0.5-50%GO)
%     S.GUI.Type2 = 0.5; %Probability of trial type 2/NOGO TRial--it doesn't have to be defined
    %%%%%%%for grouping
    %     S.GUIPanels.Task = {'TrainingLevel', 'RewardAmount'}; % GUIPanels organize the parameters into groups.
end

%--- Initialize panels
BpodParameterGUI('init', S); % Initialize parameter GUI plugin
TotalRewardDisplay('init'); %initialize the water consumption tracker
BpodNotebook('init'); % Launches an interface to write notes about

% Define trials
MaxTrials = 1000; % Set to some sane value, for preallocation
rng('shuffle')   % Reset pseudorandom seed--do it always!!!!matlab is not random

%---TrialTypes for go/nogo
TrialType0 = zeros(1,MaxTrials)+2; %All NOGO trials
TrialType100 = zeros(1,MaxTrials)+1; %All GO trials

%Generates the random array of the two trial types in the given percentage
%GO/NOGO 50-50%
MaxSame=3; %maximum number of repeat of the sam trialtype
TrialType50 = ceil(rand(1,MaxTrials)*2);
for i=1:MaxTrials-MaxSame
    if unique(TrialType50(i:i+MaxSame-1))==1
        TrialType50(i+MaxSame)=2;
    elseif unique(TrialType50(i:i+MaxSame-1))==2
        TrialType50(i+MaxSame)=1;
    end
end

BpodSystem.Data.TrialType50 = TrialType50; % The trial type of each trial completed will be added here.

%Random ITITypes
ITITypes = randi([3,6],1,MaxTrials); %there is repeat and not limited

%Save calculated parameters
BpodSystem.Data.TrialType0 = TrialType0; % Predefined TrialTypes
BpodSystem.Data.TrialType100 = TrialType100; % Predefined TrialTypes
BpodSystem.Data.TrialType = [];
BpodSystem.Data.ITITypes = ITITypes; % Predefined ITITypes, saved at the beginning

%Define variables for the calculation
% TrialNumber = 0; %probably not needed
% cTrialTypes = 0; %probably not needed
TotalCorrect = 0;
hits = 0;
correctRejection = 0;
GO = 0;
NOGO = 0;

%% Define stimuli and send to HIFI sound module
SF = 192000; % Use max supported sampling rate
H.SamplingRate = SF;
Sound = GenerateSineWave(SF, S.SinWaveFreq, S.SoundDuration)*.9; % Sampling freq (hz), Sine frequency (hz), duration (s) %.9?
H.DigitalAttenuation_dB = -20; % Set a comfortable listening level for most headphones (useful during protocol dev).
H.load(1, Sound);

%% Initialize plots
BpodSystem.ProtocolFigures.SideOutcomePlotFig = figure('Position', [914 649 1000 220],'name','Outcome plot','numbertitle','off', 'MenuBar', 'none', 'Resize', 'off');
BpodSystem.GUIHandles.SideOutcomePlot = axes('Position', [.075 .35 .89 .55]);
SideOutcomePlot(BpodSystem.GUIHandles.SideOutcomePlot,'init',2-TrialType50);  %can be a PROBLEM!

%ideas how to modify the size and name the rows--from sensory code
% BpodSystem.ProtocolFigures.OutcomePlotFig = figure('Position', [400 400 500 300],'Name','Outcome plot','numbertitle','off', 'MenuBar', 'none', 'Resize', 'on');
% BpodSystem.GUIHandles.OutcomePlot = axes('Position', [.16 .3 .8 .6]);
% OutcomePlot_Pavlov(BpodSystem.GUIHandles.OutcomePlot,'init', 1-(TrialTypes), (TrialTypes),[],MTrialNum);

%% Main loop (runs once per trial)
for currentTrial = 1:MaxTrials
    S = BpodParameterGUI('sync', S); % Sync parameters with BpodParameterGUI plugin
    %     V = GetValveTimes(S.GUI.RewardAmount, 1); LeftValveTime = V(1); %
    %     Update reward amounts, if I modify during the trial
    V = GetValveTimes(S.GUI.RewardAmount, [1]);
    RewardValveTime = V(1);
    
    cITI = ITITypes(currentTrial);
    %     LoadSerialMessages('HiFi1', {['P' 3]});  % Set serial message 1 this
    %     is sound 4
    
    %Trial parameters (for sma)

    if  S.GUI.Type1 == 1 % All GO trials
        TrialTypes = BpodSystem.Data.TrialType100;
    elseif S.GUI.Type1 == 2 % All NOGO trials
        TrialTypes = BpodSystem.Data.TrialType0;    
    elseif S.GUI.Type1 == 0.5 % All GO trials
        TrialTypes = BpodSystem.Data.TrialType50;
    else
        warning('Not a correct trial type')
    end
    
    switch TrialTypes(currentTrial) % Determine trial-specific state matrix fields
        case 1  %GO Trial: whisker stim protocol-rewarded
            ToneDelivery = {'HiFi1', ['P' 1]}; %connection port with soundboard
             WhiskStimDelivery = {'BNC1', 1, 'LED', 1}; %connection with stim.gen. send TTL signal (BNC conn)
            RewardDelivery = {'ValveState', 1};%water reward
            Action1 = 'Error';
            Action2 = 'Reward';
            
        case 2 %NOGO Trial
            ToneDelivery = {'HiFi1', ['P' 1]}; %connection port with soundboard
            WhiskStimDelivery = {'BNC2', 1, 'LED', 1}; %connection with stim.gen. send TTL signal (BNC conn); {'BNC2', 1, 'Wire', 1};
            RewardDelivery = {};%nothing happens
            Action1 = 'Reward';
            Action2 = 'Error';
    end
    
    
    
    %     OutputActionArgument = {'HiFi1', ['P' 1], 'BNCState', 1};--other
    %     version
    
    
    % Assemble state matrix
    sma = NewStateMatrix();
    %     sma = SetGlobalTimer(sma, 1, S.SoundDuration + Delay(currentTrial));
    sma = AddState(sma,'Name', 'StartState', ...
        'Timer', S.StartState,...
        'StateChangeConditions', {'Tup', 'ToneState','Port1In','EarlyDetect'},...
        'OutputActions', {});
    
    sma = AddState(sma,'Name', 'EarlyDetect', ...
        'Timer', 0,...
        'StateChangeConditions', {'Tup', 'StartState',},...
        'OutputActions', {});
    
    sma = AddState(sma, 'Name', 'ToneState', ...
        'Timer', S.SoundDuration,...
        'StateChangeConditions', {'Tup','StimState'},...
        'OutputActions', ToneDelivery);   % play tone, activating HIFI
    
    sma = AddState(sma, 'Name','StimState', ...
        'Timer', S.WhiskerStim,...
        'StateChangeConditions', {'Tup','ResponseState'},...
        'OutputActions', WhiskStimDelivery);
    
    sma = AddState(sma, 'Name', 'ResponseState', ...
        'Timer',S.ResponseTime,...
        'StateChangeConditions', {'Tup',Action1,'Port1In', Action2},...
        'OutputActions', {});
    
    sma = AddState(sma,'Name', 'Reward', ...
        'Timer',RewardValveTime,...
        'StateChangeConditions', {'Tup', 'DrinkingTime'},...
        'OutputActions', RewardDelivery);   % deliver water
    
    sma = AddState(sma,'Name', 'Error', ...
        'Timer',RewardValveTime,...
        'StateChangeConditions', {'Tup', 'DrinkingTime'},...
        'OutputActions', {});   % deliver water
    
    sma = AddState(sma, 'Name', 'DrinkingTime', ...
        'Timer',S.DrinkingTime, ...
        'StateChangeConditions', {'Tup', 'ITI'}, ...
        'OutputActions', {});  %drinking
    
    sma = AddState(sma,'Name','ITI',...
        'Timer',cITI,...
        'StateChangeConditions',{'Tup','exit'},...
        'OutputActions',{});
    
    SendStateMatrix(sma); % Send state machine to the Bpod state machine device
    RawEvents = RunStateMatrix; % Run the trial and return events
    %--- Package and save the trial's data, update plots
    if ~isempty(fieldnames(RawEvents)) % If you didn't stop the session manually mid-trial
        BpodSystem.Data = AddTrialEvents(BpodSystem.Data,RawEvents); % Adds raw events to a human-readable data struct
        %BpodSystem.Data = BpodNotebook('sync', BpodSystem.Data); % Sync with Bpod notebook plugin
        BpodSystem.Data.TrialSettings(currentTrial) = S; % Adds the settings used for the current trial to the Data struct (to be saved after the trial ends)
        BpodSystem.Data.TrialTypes(currentTrial) = TrialTypes(currentTrial); % Adds the trial type of the current trial to data    
        SaveBpodSessionData; % Saves the field BpodSystem.Data to the current data file
        UpdateSideOutcomePlot(TrialTypes, BpodSystem.Data); %% CAN BE PROBLEM--TEST IT
        UpdateTotalRewardDisplay(S.GUI.RewardAmount, currentTrial); %calculate the water consumption
        BpodSystem.Data = BpodNotebook('sync', BpodSystem.Data); %not sure of the place of this/in the saving part?
    end
    
    %--- This final block of code is necessary for the Bpod console's pause and stop buttons to work
    HandlePauseCondition; % Checks to see if the protocol is paused. If so, waits until user resumes.
    if BpodSystem.Status.BeingUsed == 0
        return
    end
    
    
    %% Calculate and show reults after each trial------have to check if it works???
    TrialNumber = BpodSystem.Data.nTrials; %This way analysis will always run on meaningful data(wont try to analize free water for example)
    cTrialTypes = BpodSystem.Data.TrialTypes; %HAVE to check!!!
    
    if isnan(BpodSystem.Data.RawEvents.Trial{1, TrialNumber}.States.Reward(1,1))
    else
        TotalCorrect = TotalCorrect + 1;
    end
    
    if TrialTypes(currentTrial) == 1
        if isnan(BpodSystem.Data.RawEvents.Trial{1, TrialNumber}.States.Reward(1,1))
        else
            hits = hits + 1;
        end
    elseif TrialTypes(currentTrial) == 2
        if isnan(BpodSystem.Data.RawEvents.Trial{1, TrialNumber}.States.Reward(1,1))
        else
            correctRejection = correctRejection + 1;
        end
        
    else
        warning('Something went wrong')
    end
    
    
        %Calculate ratio
        Hits = hits;
        GO = sum(cTrialTypes(:) == 1);
        CorrectRejection = correctRejection;
        NOGO = sum(cTrialTypes(:) == 2);
    
    %This has letter coding with the numbers, choose whichever you prefer
    fprintf('TrialNum:%d GO:%d TotalHits:%d NOGO:%d CorrectRejection:%d \n',TrialNumber,GO,Hits,NOGO,CorrectRejection);
    
end

end
% -------------------------------------------------------------------------
%--- Typically a block of code here will update online plots using the newly updated BpodSystem.Data

function UpdateSideOutcomePlot(TrialTypes, Data)
% Determine outcomes from state data and score as the SideOutcomePlot plugin expects
global BpodSystem
Outcomes = zeros(1,Data.nTrials);
for x = 1:Data.nTrials
    if ~isnan(Data.RawEvents.Trial{x}.States.Reward(1))
        Outcomes(x) = 1;
    elseif ~isnan(Data.RawEvents.Trial{x}.States.Error(1))
        Outcomes(x) = 0;
    else
        Outcomes(x) = 3;
    end
end

SideOutcomePlot(BpodSystem.GUIHandles.SideOutcomePlot,'update',Data.nTrials+1,2-TrialTypes,Outcomes);
end



%Update reward amount
function UpdateTotalRewardDisplay(RewardAmount, currentTrial)
% If rewarded based on the state data, update the TotalRewardDisplay
global BpodSystem
if BpodSystem.Data.TrialTypes(currentTrial) == 1
    if ~isnan(BpodSystem.Data.RawEvents.Trial{currentTrial}.States.Reward(1))
        TotalRewardDisplay('add', RewardAmount);
    end
else
end
end


