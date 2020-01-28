import collections
import os
import re
import subprocess
import sys
import wexpect

class Video:
    def __init__(self, input_path):
        self.input_path = os.path.abspath(input_path)

    def encode_settings(self):
        # Parse input (directory vs file vs json)
        video_files = []
        if os.path.isdir(self.input_path):
            for root, dirs, files in os.walk(self.input_path):
                for file in files:
                    if file.endswith(('.mkv', '.mp4', '.avi')):
                        video_files.append(os.path.join(root, file))
        elif os.path.isfile(self.input_path):
            if self.input_path.endswith('.json'):
                # JSON read
            elif self.input_path.endswith(('.mkv', '.mp4', '.avi')):
                video_files.append(os.path.join(root, file))
        elif os.path.isfile(self.input_path):
            video_files.append(self.input_path)
        else:
            print('The input path is not a valid file or directory.')
        
        # Movie or TV
        if len(video_files) > 1:
            ismovie = input('Are these videos episodes of ? (m/n): ')
        else:
            ismovie = input('Is this video a movie or a TV episode? (y/n): ')
        if ismovie == 'y':
            
        
        # Video Title
        video_title = input('\nWhat is the title of this movie or TV show?\n'
            + 'For movies, use the format "Movie Title (YYYY)", '
            + 'and for TV, use the format "TV Show - SxxExx - Title"\n'
            + 'Title: ')
        
        # Encoding Setting
        encode_setting = input('What encode setting would you like to run?\n'
            + '\t[1] 2160p - reference\n'
            + '\t[2] 2160p - regular\n'
            + '\t[3] 1080p - reference\n'
            + '\t[4] 1080p - regular / series\n'
            + 'Setting: ')
            
        # Animation Flag
        animation = input('Is the source animated? (y/n): ')
        
        for input_video in video_files:
            self.encode_video(input_video, video_title, encode_setting, animation)
    
    def encode_video(self, input_video, video_title, encode_setting, animation):
        x265params = 'sao=0:selective-sao=0'
        
        print('\nReading video characteristics...')
        color_range = self.mediainfo(input_video, 'Video', 'colour_range')
        color_prim = self.mediainfo(input_video, 'Video', 'colour_primaries')
        color_matrix = self.mediainfo(input_video, 'Video', 'colour_matrix')
        transfer_char = self.mediainfo(input_video, 'Video', 'transfer_characteristics')
        audio_format = re.match(r'^[^\/]+', self.mediainfo(input_video, 'General',
            'Audio_Format_List')).group(0).rstrip()
        if color_range == 'Limited':
            x265params += ':range=limited'
            print('\tColor range is: Limited')
        elif color_range == 'Full':
            x265params += ':range=full'
            print('\tColor range is: Full')
        else:
            print('No color range detected.')
        if 'BT.709' in [color_prim, color_matrix, transfer_char]:
            x265params += ':colorprim=bt709:colormatrix=bt709:transfer=bt709'
            print('\tBT.709 color profile detected')
        
        # Need to add UHD color settings (--colorprim bt2020 --transfer smpte2084) & max-cll/master-display

        if encode_setting in ['1', '3']:
            encode_crf = '17'
            encode_preset = 'slow'
        elif encode_setting in ['2', '4']:
            encode_crf = '19'
            encode_preset = 'slow'
        if encode_setting in ['1', '2']:
            x265params += (':hdr-opt=1:repeat-headers=1:no-open-gop=1'
                + ':min-keyint=1:keyint=120:level-idc=51:aud=1'
                + ':chromaloc=2:hrd:master-display=*:max-cll=*')
            encode_resolution = 'Bluray-2160p'
        else:
            encode_resolution = 'Bluray-1080p'
        
        if animation == 'y':
            x265params += ':tune=animation'
        else:
            x265params += ':deblock=-1,-1'
        
        crop_dim = self.get_crop_dimension(input_video)
        
        print('Encoding with the following settings:\n'
            + '\tCRF: {}\n'.format(encode_crf)
            + '\tPreset: {}\n'.format(encode_preset)
            + '\tx265 parameters: {}\n'.format(x265params)
            + '\tCrop: {}\n'.format(crop_dim))

        print('\nEncoding with ffpmeg...\n')
        args = ['ffmpeg', '-analyzeduration', '2147483647', '-probesize',
            '2147483647', '-i', '{}'.format(input_video), '-map', '0',
            '-c', 'copy',  '-c:v', 'libx265', '-pix_fmt', 'yuv420p10le',
            '-crf', '{}'.format(encode_crf), '-preset', '{}'.format(
            encode_preset), '-x265-params', '{}'.format(x265params), '-vf',
            'crop={}'.format(crop_dim), '-y',
            'E:\Processing\encodes\{} - {} x265 {}.mkv'.format(
            video_title, encode_resolution, audio_format)]
        ffmpeg_encode = subprocess.run(args, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True).stdout
        print('Done!')
        
        """cmd = ('ffmpeg -analyzeduration 2147483647 -probesize 2147483647 -i '
            + '"{}" '.format(input_video) + '-map 0 -c copy -c:v libx265 '
            + '-pix_fmt yuv420p10le -crf {} '.format(encode_crf) + '-preset '
            +'{} '.format(encode_preset) + '-x265-params {} '.format(x265params)
            + '-vf crop={} '.format(crop_dim) + '-y "E:\Processing\encodes\'
            + '{} - {} x265 {}.mkv"'.format(video_title, encode_resolution,
                audio_format))
        https://stackoverflow.com/questions/7632589/getting-realtime-output-from-ffmpeg-to-be-used-in-progress-bar-pyqt4-stdout"""

    def mediainfo(self, input_video, category, parameter):
        query = '--Output={};%{}%'.format(category, parameter)
        args = ['MediaInfo', '{}'.format(input_video), query]
        mediainfo = subprocess.run(args, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True).stdout
        return mediainfo.strip()

    # def mkv_clean(self):
        

    def get_movie_length(self, input_video):
        args = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            '{}'.format(input_video)]
        ffprobe = subprocess.run(args, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True).stdout
        return float(ffprobe)

    def get_crop_dimension(self, input_video):
        def ffmpeg_cropdetect(ss):
            args = ['ffmpeg', '-ss', '{}'.format(ss), '-i',
                '{}'.format(input_video), '-t', '120', '-an', '-vf',
                'cropdetect', '-f', 'matroska', '-y', '-crf', '51', '-preset',
                'ultrafast', 'NUL']
            ffmpeg_output = subprocess.run(args, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True).stdout
            pattern = re.compile('crop=([0-9]+:[0-9]+:[0-9]+:[0-9]+)')
            crop_list = pattern.findall(ffmpeg_output)
            return crop_list
        
        print('Detecting black bars for cropping...')
        movie_length = self.get_movie_length(input_video)
        crop_list = []
        for x in range(1,4):
            location = (movie_length / 4)*x
            print('\tChecking at time: ' + str(location))
            crop_list += ffmpeg_cropdetect(location)
        crop_count = collections.Counter(crop_list)
        crop_most_common = crop_count.most_common(1)[0][0]
        print('\tPossible crop dimensions: ' + str(crop_count))
        print('\tMost common dimension: ' + crop_most_common)
        return crop_most_common


encode = Video(sys.argv[1]).encode_settings()
