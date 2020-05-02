#!/usr/bin/python
import sys, getopt  # parse script arguments
import os  # search directories
from moviepy.editor import *  # movie editor
import youtube_dl  # download mp3 songs


def getMusicDir(links_path):
    return "/".join(links_path.split("/")[:-1]) + "/"


def downloadMusic(links_path="/home/robot/Documents/video-edit/files/music/links.txt"):
    # get the links file's folder, so the songs are stored in there
    music_dir = getMusicDir(links_path)
    with open(links_path, "r") as f:
        music_links = f.read().splitlines()
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": music_dir + "%(title)s.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(music_links)


# import files in the folder that have the mp3 extension
def importMusic(music_dir="/home/robot/Documents/video-edit/files/music/"):
    music_path = [music_dir + s for s in os.listdir(music_dir) if s.endswith("mp3")]
    musics = list(map(AudioFileClip, music_path))
    return musics


# import videos in the folder that have the mp4 extension
def importVideos(
    video_dir="/home/robot/Documents/video-edit/files/videos/", order="date"
):
    # videos must have the same size, so we make sure they do
    def importClip(video_path):
        video = VideoFileClip(video_path)
        # check if the video is horizontal or vertical
        if video.w > video.h:
            # if not 1080p, make it
            if video.w != 1920:
                video = video.resize(width=1920)
        else:
            # if not 1080p, make it
            if video.h != 1080:
                video = video.resize(height=1080)
        return video

    video_path = [video_dir + s for s in os.listdir(video_dir) if s.endswith("mp4")]
    print(order)
    if order == "name":
        print(video_path)
        video_path.sort()
        print(video_path)
    else:  # default order by date
        video_path.sort(key=os.path.getmtime)

    return list(map(importClip, video_path))


def joinVideoMusic(
    filename, videos, music, codec="libx264", volumeX=0.2, bitrate="20M"
):
    # normalize each video's audio individually
    videos = list(map(lambda v: v.fx(afx.audio_normalize), videos))
    # normalize music audio and then multiply the volume by factor volumeX
    music = list(
        map(lambda m: m.fx(afx.audio_normalize).fx(afx.volumex, volumeX), music)
    )

    # compose so we can have horizontal and vertical videos
    final_video = concatenate_videoclips(videos, method="compose")
    # join video audios and background music and make sure it has the same duration as the video
    final_audio = CompositeAudioClip(
        [
            final_video.audio,
            concatenate_audioclips(music).set_duration(final_video.duration),
        ]
    )
    # set audio
    final = final_video.set_audio(final_audio)
    print(filename)
    os.chdir("/".join(filename.split("/")[:-1]))
    # save the movie
    final.write_videofile(
        filename.split("/")[-1],
        fps=30,
        audio_bitrate="3200k",
        bitrate=bitrate,
        codec=codec,
    )

    print("Video file written to: " + filename)


def main(argv):
    cwd = os.getcwd()
    links_path = cwd + "/files/music/links.txt"
    video_dir = cwd + "/files/videos/"
    music_dir = None
    dest_path = cwd + "/result.mp4"
    codec = "libx264"
    bitrate = "20M"
    gain = 0.2
    order = "date"
    try:
        opts, args = getopt.getopt(
            argv,
            "hl:v:m:d:c:b:g:o:",
            [
                "links-file=",
                "videos-dir=",
                "music-dir=",
                "destination=",
                "codec=",
                "bitrate=",
                "gain=",
                "order=",
                "help",
            ],
        )
    except getopt.GetoptError:
        print(
            "video-edit.py -b <bitrate> -c <codec> -d <destination> -g <volumegain> -l <linksfile> -m <musicdir> -o <orderby> -v <videosdir>"
        )
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(
                "video-edit.py -b <bitrate> -c <codec> -d <destination> -g <volumegain> -l <linksfile> -m <musicdir> -o <orderby> -v <videosdir>"
            )
            sys.exit()
        elif opt in ("-b", "--bitrate"):
            bitrate = arg
        elif opt in ("-c", "--codec"):
            codec = arg
        elif opt in ("-d", "--destination"):
            dest_path = arg
        elif opt in ("-g", "--volume"):
            gain = float(arg)
        elif opt in ("-l", "--links-file"):
            links_path = arg
        elif opt in ("-m", "--music-file"):
            music_dir = arg
        elif opt in ("-o", "--order"):
            order = arg
        elif opt in ("-v", "--videos-dir"):
            video_dir = arg

    if music_dir is None:
        downloadMusic(links_path=links_path)
        music_dir = getMusicDir(links_path)

    music = importMusic(music_dir=music_dir)
    videos = importVideos(video_dir=video_dir, order=order)

    joinVideoMusic(dest_path, videos, music, bitrate=bitrate, codec=codec, volumeX=gain)


if __name__ == "__main__":
    main(sys.argv[1:])
