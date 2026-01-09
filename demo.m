%标记com和dannce都是用此文件
clear all
addpath(genpath('deps'));
projectFolder = 'G:\Li_lab\lst_3d\dannce_Label3D\looming_DOM_wrx';
skeletonPath=fullfile(projectFolder, 'skeletons\com.mat');%更改.mat
skeleton = load(skeletonPath);
calibPaths = collectCalibrationPaths(projectFolder);
params = cellfun(@(X) {load(X)}, calibPaths);

vidName = '0.avi';
vidPaths = collectVideoPaths(projectFolder,vidName);
videos = cell(5,1);% 
sync =  collectSyncPaths(projectFolder, '*.mat');
sync = cellfun(@(X) {load(X)}, sync);
%% 指定需要标记的帧序号
%framesIndex1=650:2:750;
%framesToLabel= cat(2,framesIndex1,framesIndex2);
framesToLabel=1:30:3000; % 需要读到第3000帧，此数越小越快
% 内存最多读500帧 
%%
for nVid = 1:numel(vidPaths)
    frameInds = sync{nVid}.data_frame(framesToLabel);
    videos{nVid} = readFrames(vidPaths{nVid}, frameInds+1,false);
end

%% Start Label3D
%close all
labelGui = Label3D(params, videos, skeleton, 'sync', sync,'framesToLabel', framesToLabel,'savePath',projectFolder);%load from scratch
%labelGui=Label3D("G:\Li_lab\lst_3d\dannce_Label3D\label_project\20241122_150635_Label3D_videos.mat") %打开之前保存的文件%加载saveAll()保存的文件
%%  Save to *dannce.mat 
%不论标记dannce或com输出标记文件均为dannce.mat
%labelGui.exportDannce('basePath',danncePath,'saveFolder','save_dannce');
%labelGui.saveAll()%退出时执行，保存进度

%labelGui.exportDannce %不再标记，导出文件后直接退出
%labelGui.saveAll() %还要继续标记，不会关闭matlab
%上述两个命令2选1，导出文件不可覆盖
%% Check the camera positions
%labelGui.plotCameras%选择projectFolder打开
%% If you just wish to view labels, use View 3D
%close all
%viewGui = View3D(params, videos, skeleton);
%% You can load both in different ways
%close all;
%View3D()
%% Save current frame
frame = getframe(gcf)
imwrite(frame.cdata, 'G:\Li_lab\lst_3d\dannce_Label3D\predict_project\rearing_label_eg_127f.png');