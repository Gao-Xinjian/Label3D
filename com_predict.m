%% 用于com-train
clear;
close all;
addpath(genpath('deps'));
projectFolder = 'G:\Li_lab\lst_3d\dannce_Label3D\label_project';
skeleton=load('G:\Li_lab\lst_3d\dannce_Label3D\label_project\skeletons\com.mat');
calibPaths = collectCalibrationPaths(projectFolder);
params = cellfun(@(X) {load(X)}, calibPaths);
vidName = '0.avi';
vidPaths = collectVideoPaths(projectFolder,vidName);
videos = cell(5,1);% 
sync =  collectSyncPaths(projectFolder, '*.mat');
sync = cellfun(@(X) {load(X)}, sync);

framesToLabel =1:100;
for nVid = 1:numel(vidPaths)%每次循环处理一个视频文件
    frameInds = sync{nVid}.data_frame(framesToLabel);%
    videos{nVid} = readFrames(vidPaths{nVid}, frameInds+1,true);
end

%labelGui=Label3D('com3d_0.mat',params,videos,skeleton,sync,framesToLabel);
%labelGui.saveAll();

%%
%load G:\Li_lab\lst_3d\dannce_Label3D\label_project\com3d_0.mat;
framesToLabel=sampleID;
data_3D=com;

save com_basic.mat  data_3D -append

%params=camParams;
%labelGui=Label3D("com3d_0.mat",params,videos,skeleton,sync,framesToLabel);
%%
for i=1:length(sync)
    struct_cell=sync(i);
    struct=sync{1};
    fields = fieldnames(struct);
    for j=1:length(fields)
        tmp=fields(i);
        tmp_edit=tmp(750:end,:);
    end
end

%%
sync =  collectSyncPaths('G:\Li_lab\lst_3d\dannce_Label3D\label_project\sync', '*.mat');
sync = cellfun(@(X) {load(X)}, sync);
%%
viewGui = View3D(params, videos, skeleton);