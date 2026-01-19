"""
Use this script to resample videos to a uniform frame rate and frame count, and create sync files.

This script:
1. Reads video files from different camera subdirectories
2. Calculates uniform target frame count based on maximum video duration
3. Resamples all videos to the same target frame rate and frame count (preserves all content)
4. Generates synchronization files for the resampled videos

Use of resampleAndSyncFiles.py:
    python resampleAndSyncFiles.py path_to_video_folder target_frame_rate num_landmarks

path_to_video_folder: string, the path to your project main video folder, which
    contains separate subfolders for each camera. These subfolders contain the
    video files.
target_frame_rate: int or float, the target frame rate to resample all videos to
num_landmarks: number of landmarks you plan to label/track

Resampled videos will be written to a `video_resampled` directory in the video folder parent directory.
Sync files will be written to a `sync` directory in the video folder parent directory.
"""

import imageio
import numpy as np
import scipy.io as sio
import os
import sys
from tqdm import tqdm

_VALID_EXT = ["mp4", "avi"]


def count_frames_safe(path, show_progress=False, desc="Counting frames"):
    """Count frames by iterating sequentially (most reliable for mixed codecs)."""
    reader = imageio.get_reader(os.path.abspath(path))
    count = 0
    iterator = reader
    if show_progress:
        iterator = tqdm(iterator, desc=desc, leave=False)
    try:
        for _ in iterator:
            count += 1
    except Exception:
        pass
    finally:
        reader.close()
    return count

def get_vid_paths(dir_):
    """Get all valid video file paths from a directory"""
    vids = os.listdir(dir_)
    vids = [vd for vd in vids if vd.split(".")[-1] in _VALID_EXT]
    vids = [os.path.join(dir_, vd) for vd in vids]
    return vids

if __name__ == "__main__":
    vidpath = sys.argv[1]
    target_fps = float(sys.argv[2])
    num_landmarks = int(sys.argv[3])
    
    # Setup output paths
    parent_dir = os.path.dirname(vidpath.rstrip(os.sep))
    vidpath_basename = os.path.basename(vidpath)
    resampled_outpath = os.path.join(parent_dir, vidpath_basename + "_resampled")
    sync_outpath = os.path.join(parent_dir, "sync")
    
    if not os.path.exists(resampled_outpath):
        os.makedirs(resampled_outpath)
        print(f"Created resampled directory: {resampled_outpath}")
    
    if not os.path.exists(sync_outpath):
        os.makedirs(sync_outpath)
        print(f"Created sync directory: {sync_outpath}")
    
    print(f"Reading videos from {vidpath}...")
    print(f"Target frame rate: {target_fps} fps\n")
    
    # Find camera directories
    dirs = os.listdir(vidpath)
    dirs = [d for d in dirs if os.path.isdir(os.path.join(vidpath, d))]
    dirs = [d for d in dirs if d not in ['data', 'Camera0']]
    print(f"Found the following cameras: {dirs}\n")
    
    dirs = [os.path.join(vidpath, d) for d in dirs]
    
    # Step 1: Collect video information
    print("=" * 60)
    print("STEP 1: Analyzing video durations")
    print("=" * 60 + "\n")
    
    camnames = []
    video_info = {}
    durations = []
    
    for d in dirs:
        vids = get_vid_paths(d)
        if len(vids) == 0:
            print("Traversing video subdirectory")
            d = os.path.join(d, os.listdir(d)[0])
            vids = get_vid_paths(d)
        
        cname = os.path.basename(d.rstrip(os.sep))
        camnames.append(cname)
        
        total_duration = 0
        frames_info = []
        
        for vid_path in vids:
            reader = imageio.get_reader(os.path.abspath(vid_path))
            fps = reader.get_meta_data()['fps']
            num_frames = count_frames_safe(
                vid_path,
                show_progress=True,
                desc=f"Counting {os.path.basename(vid_path)}"
            )
            duration = num_frames / fps
            total_duration += duration
            frames_info.append({
                'path': vid_path,
                'fps': fps,
                'num_frames': num_frames,
                'duration': duration
            })
            reader.close()
        
        video_info[cname] = {
            'total_duration': total_duration,
            'frames_info': frames_info
        }
        durations.append(total_duration)
        print(f"{cname}: {total_duration:.2f} seconds, {frames_info} frames, ({len(vids)} file(s))")

    # Get maximum frame count from all videos (direct approach, no rounding errors)
    max_frames = 0
    for cname in camnames:
        for info in video_info[cname]['frames_info']:
            max_frames = max(max_frames, info['num_frames'])
    
    target_frames = max_frames
    print(f"\nMaximum frame count across all cameras: {target_frames} frames\n")
    
    # Step 2: Resample all videos to target frame count
    print("=" * 60)
    print("STEP 2: Resampling videos")
    print("=" * 60 + "\n")
    
    for cname in camnames:
        cam_resampled_dir = os.path.join(resampled_outpath, cname)
        if not os.path.exists(cam_resampled_dir):
            os.makedirs(cam_resampled_dir)
        
        frames_info = video_info[cname]['frames_info']
        current_duration = video_info[cname]['total_duration']
        
        # Build frame index without loading frames into memory
        frame_index = []  # (video_info, frame_idx, normalized_timestamp)
        time_offset = 0
        
        for info in frames_info:
            for frame_idx in range(info['num_frames']):
                # Normalize timestamp to [0, 1]
                timestamp = (time_offset + frame_idx / info['fps']) / current_duration
                frame_index.append((info, frame_idx, timestamp))
            time_offset += info['duration']
        
        print(f"Processing {cname}...")
        print(f"  Source: {len(frame_index)} frames over {current_duration:.2f} seconds")
        print(f"  Target: {target_frames} frames at {target_fps} fps")
        
        # Resample by selecting frames at uniform time intervals
        target_timestamps = np.linspace(0, 1, target_frames)
        source_timestamps = np.array([item[2] for item in frame_index])
        
        # Create output writer
        output_vid_path = os.path.join(cam_resampled_dir, os.path.basename(frames_info[0]['path']))
        writer = imageio.get_writer(output_vid_path, fps=target_fps)
        
        # For each target timestamp, find and load nearest source frame
        # Group frames by source video to minimize reader open/close operations
        target_frames_info = []
        for target_ts in target_timestamps:
            idx = np.argmin(np.abs(source_timestamps - target_ts))
            target_frames_info.append(frame_index[idx])
        
        # Process frames in order, opening each video file only once
        current_reader = None
        current_path = None
        
        for info, frame_idx, timestamp in tqdm(target_frames_info, desc="Resampling frames"):
            video_path = os.path.abspath(info['path'])
            
            # Open new reader if video file changed
            if current_path != video_path:
                if current_reader is not None:
                    current_reader.close()
                current_reader = imageio.get_reader(video_path)
                current_path = video_path
            
            try:
                frame = current_reader.get_data(frame_idx)
                writer.append_data(frame)
            except (IndexError, RuntimeError) as e:
                print(f"Warning: Failed to read frame {frame_idx} from {video_path}: {e}")
                # Use black frame as fallback
                if len(target_frames_info) > 0:
                    # Get frame shape from first successful frame
                    try:
                        dummy_frame = current_reader.get_data(0)
                        black_frame = np.zeros_like(dummy_frame)
                        writer.append_data(black_frame)
                    except:
                        pass
        
        if current_reader is not None:
            current_reader.close()
        
        writer.close()
        print(f"  Written: {target_frames} frames\n")
    
    # Step 3: Generate sync files
    print("=" * 60)
    print("STEP 3: Generating sync files")
    print("=" * 60 + "\n")
    
    fp = 1000.0 / target_fps  # frame period in ms
    
    data_frame = np.arange(target_frames).astype("float64")
    data_sampleID = data_frame * fp + 1
    data_2d = np.zeros((target_frames, 2 * num_landmarks))
    data_3d = np.zeros((target_frames, 3 * num_landmarks))
    
    checkf = os.listdir(sync_outpath)
    for cname in camnames:
        fname = cname + "_sync.mat"
        outfile = os.path.join(sync_outpath, fname)
        
        if fname in checkf:
            ans = ""
            while ans != "y" and ans != "n":
                print(f"{fname} already exists. Overwrite (y/n)?")
                ans = input().lower()
            
            if ans == "n":
                print("Ok, skipping.")
                continue
        
        print(f"Writing {outfile}")
        sio.savemat(
            outfile,
            {
                "data_frame": data_frame[:, np.newaxis],
                "data_sampleID": data_sampleID[:, np.newaxis],
                "data_2d": data_2d,
                "data_3d": data_3d,
            },
        )
    
    print("\n" + "=" * 60)
    print("All tasks completed!")
    print("=" * 60)
    print(f"Resampled videos saved to: {resampled_outpath}")
    print(f"Sync files saved to: {sync_outpath}")
