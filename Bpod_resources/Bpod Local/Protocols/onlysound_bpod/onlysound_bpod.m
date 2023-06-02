function onlysound_bpod
%Testind HIFI sound board


%% Load Bpod variables and start USB connections to any modules
global BpodSystem

% Assert HiFi module is present + USB-paired (via USB button on console GUI)
BpodSystem.assertModule('HiFi', 1); % The second argument (1) indicates that the HiFi module must be paired with its USB serial port-sayingYES
% Create an instance of the HiFi module
H = BpodHiFi(BpodSystem.ModuleUSB.HiFi1); % The argument is the name of the HiFi module's USB serial port (e.g. COM3)-hopefully finds itself
% H = BpodHiFi('COM3'); % if it cannot find by itself


S = BpodSystem.ProtocolSettings; % Loads settings file chosen in launch manager into current workspace as a struct called 'S'
if isempty(fieldnames(S))  % If chosen settings file was an empty struct, populate struct with default settings
    % Define default settings here as fields of S (i.e S.InitialDelay = 3.2)
    %it doesn't appear in the GUI
    
    S.GUI.SoundDuration = 0.25; % s
    S.GUI.SinWaveFreq = 7000; %Hz
end

BpodParameterGUI('init', S); % Initialize parameter GUI plugin
%% Define trials
rng('shuffle')   % Reset pseudorandom seed
MaxTrials = 100;
TrialTypes = zeros(1,MaxTrials)+1;

%% Define stimuli and send to HIFI sound module
SF = 192000; % Use max supported sampling rate
H.SamplingRate = SF;
Sound = GenerateSineWave(SF, S.GUI.SinWaveFreq, S.GUI.SoundDuration)*.9; % Sampling freq (hz), Sine frequency (hz), duration (s) %.9?
H.DigitalAttenuation_dB = -20; % Set a comfortable listening level for most headphones (useful during protocol dev).
H.load(1, Sound);

%% Main loop
for currentTrial = 1:MaxTrials
    S = BpodParameterGUI('sync', S); % Sync parameters with BpodParameterGUI plugin
    
    
    LoadSerialMessages('HiFi1', {['P' 3]});  % Set serial message 1
    
    sma = NewStateMachine();
    sma = AddState(sma, 'Name', 'PlaySound', ...
        'Timer', 0.1,...
        'StateChangeConditions', {'Tup', 'ITI'},...
        'OutputActions', {'HiFi1', 1}); % Sends serial message 1
    sma = AddState(sma,'Name','ITI',...
        'Timer',3,...
        'StateChangeConditions',{'Tup','exit'},...
        'OutputActions',{});
    
    SendStateMachine(sma);
    RawEvents = RunStateMachine;
    
    if ~isempty(fieldnames(RawEvents)) % If you didn't stop the session manually mid-trial
        BpodSystem.Data = AddTrialEvents(BpodSystem.Data,RawEvents); % Adds raw events to a human-readable data struct
        SaveBpodSessionData; % Saves the field BpodSystem.Data to the current data file
    end
    
    %--- This final block of code is necessary for the Bpod console's pause and stop buttons to work
    HandlePauseCondition; % Checks to see if the protocol is paused. If so, waits until user resumes.
    if BpodSystem.Status.BeingUsed == 0
        return
    end
end



end