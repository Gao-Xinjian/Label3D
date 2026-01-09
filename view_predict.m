clear all
addpath(genpath('deps'));
projectFolder = 'G:\Li_lab\lst_3d\dannce_Label3D\predict_project';
calibPaths = collectCalibrationPaths(projectFolder);
params = cellfun(@(X) {load(X)}, calibPaths);
vidName = '0.avi';
vidPaths = collectVideoPaths(projectFolder,vidName);
videos = cell(5,1);%camera数量
sync =  collectSyncPaths(projectFolder, '*.mat');
sync = cellfun(@(X) {load(X)}, sync);

%% 
framesToLabel =1:10:100; %[2]查看原视频帧序号，可在工作区查看framesToLabel获得帧序号，来重新标记预测不理想的点 

for nVid = 1:numel(vidPaths)
    frameInds = sync{nVid}.data_frame(framesToLabel);
    videos{nVid} = readFrames(vidPaths{nVid}, frameInds+1,false);
end
%% view dannce predictions
skeletonPath=fullfile(projectFolder, 'skeletons\mouse_21.mat'); %[1]更改.mat文件
skeleton = load(skeletonPath);
viewGui = View3D(params, videos, skeleton);
predPath= fullfile(projectFolder,'predictions\exp_325.mat'); %[3]更改predict文件
disp(class(predPath));
disp(predPath);
%save_data_AVG0.mat为预测结果，此处已被重命名
pts3d = load(predPath);
dannce_pts=pts3d.pred(framesToLabel,:,:);
viewGui.loadFrom3D(dannce_pts);
%%  view COM predictions
skeletonPath=fullfile(projectFolder, 'skeletons\com.mat');
skeleton = load(skeletonPath);
viewGui = View3D(params, videos, skeleton);
comPath= fullfile(projectFolder,'predictions\com3d_0_M1D1_.mat');%[3]更改predict文件
pts3d = load(comPath);
com_pts=pts3d.com(framesToLabel,:); %从第0帧开始读
viewGui.loadFrom3D(com_pts);
%% write videos
framesInVideo = framesToLabel;
savePath = 'exp_325.mp4';
viewGui.writeVideo(framesInVideo, savePath, 'FPS', 5, 'Quality', 80);