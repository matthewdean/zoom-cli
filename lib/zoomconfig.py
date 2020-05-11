import sqlite3
import platform
import os
import filetype
from shutil import copyfile
import uuid
from collections import namedtuple
from pathlib import Path
import sys
import ffmpeg

from enum import Enum

VirtualBackground = namedtuple('VirtualBackground', 'path name type custom_index thumb_path')

class VirtualBackgroundType(Enum):
    DEFAULT_IMAGE = 0
    CUSTOM_IMAGE = 1
    DEFAULT_VIDEO = 2
    CUSTOM_VIDEO = 3

class ZoomConfig:
    background_path_key = 'com.zoom.client.saved.video.replace_bk_path_1'
    background_data_key = 'com.zoom.client.saved.video.replace_bk_data_1'
    background_types_custom = (VirtualBackgroundType.CUSTOM_IMAGE.value, VirtualBackgroundType.CUSTOM_VIDEO.value)
    background_types_image = (VirtualBackgroundType.DEFAULT_IMAGE.value, VirtualBackgroundType.CUSTOM_IMAGE.value)
    background_types_video = (VirtualBackgroundType.DEFAULT_VIDEO.value, VirtualBackgroundType.CUSTOM_VIDEO.value)

    def __init__(self, data_dir):
        self.backgrounds_dir = data_dir / "VirtualBkgnd_Custom"
        self.video_thumbs_dir = data_dir / "VirtualBkgnd_VideoThumb"
        self.conn = sqlite3.connect(data_dir / "zoomus.db")
        if platform.system() == "Windows":
            self.ffmpeg_path = str(Path(__file__).parent / "bin" / "ffmpeg-win64" / "bin" / "ffmpeg.exe")
        elif platform.system() == "Darwin":
            self.ffmpeg_path = str(Path(__file__).parent / "bin" / "ffmpeg-macos" / "bin" / "ffmpeg")
        else:
            raise Exception("not implemented")

    def get_background(self):
        return self.get_current_background_path()

    def export_backgrounds(self, export_dir):
        Path(export_dir).mkdir(exist_ok=True)

        for background in self.get_backgrounds():
            source_path = background.path.encode("utf-8")
            target_path = os.path.join(background.name.encode("utf-8"),
                background.name.encode("utf-8"))

            # append file extension if we can infer one
            kind = filetype.guess(source_path)
            if kind:
                target_path += ".".encode("utf-8") + \
                    kind.extension.encode("utf-8")

            copyfile(source_path, target_path)

    def import_background(self, source_path):
        kind = filetype.guess(source_path)
        if kind is None:
            print("skipping file because unable to determine format: " + source_path)
            return

        target_path = None
        name = Path(source_path).stem
        type = None
        custom_index = None
        thumb_path = None

        if kind.mime.startswith("image"):
            type = VirtualBackgroundType.CUSTOM_IMAGE
            # copy the image to the zoom virtual backgrounds directory
            target_path = str(self.backgrounds_dir / str(uuid.uuid4()))

            # todo: change this to generate PNGs
            ffmpeg.input(source_path).filter('scale', 'min(in_w,1920)', -1).filter('crop', 'min(in_w,1920)', 'min(in_h,1080)', 0, '(max(in_w-1080,0))/2').output(target_path, format='mjpeg').run(cmd=self.ffmpeg_path)
            # copyfile(source_path, target_path)

        elif kind.mime.startswith("video"):
            type = VirtualBackgroundType.CUSTOM_VIDEO
            # we do not copy videos, presumably for size
            target_path = source_path

            # generate video thumbnail
            thumb_path = str(self.video_thumbs_dir / str(uuid.uuid4()))
            # todo: change this to generate BMPs
            ffmpeg.input(source_path).filter('scale', 320, -1).output(thumb_path, format='mjpeg', vframes=1).run(cmd=self.ffmpeg_path)
        else:
           print("skipping file for unsupported mime type: " + kind.mime + " from " + source_path)
           return

        custom_index = type.value * 100
        background = VirtualBackground(path=target_path, name=name, type=type.value, custom_index=custom_index, thumb_path=thumb_path)
        c = self.conn.cursor()
        c.execute('INSERT OR IGNORE INTO zoom_conf_video_background_a (path,name,type,customIndex,thumbPath) VALUES(?,?,?,?,?)', background)
        self.conn.commit()

        return background

    def import_backgrounds(self, source_path):
        root = Path(source_path)
        if root.is_dir():
            for child in root.iterdir():
                if child.is_file():
                    print(child.resolve())
                    self.import_background(str(child.resolve()))
        elif root.is_file():
            self.import_background(source_path)
        else:
            raise Exception("import called on something that is neither a file nor directory: " + source_path)

    def get_current_background_path(self):
        c = self.conn.cursor()
        c.execute('SELECT value FROM zoom_kv WHERE key=?', (ZoomConfig.background_path_key,))
        row = c.fetchone()
        if row:
            return row[0]
        else:
            return None

    def remove_current_background(self):
        c = self.conn.cursor()
        c.execute('DELETE FROM zoom_kv WHERE key=?', (ZoomConfig.background_path_key,))
        self.conn.commit()

    def set_background(self, path):
        self.remove_current_background()
        if not path:
            return

        # validate that the file exists
        p = Path(path)
        if not p.exists():
            raise Exception("file not found: " + path)
        elif not p.is_file():
            raise Exception("cannot set background to a non-file: " + path)

        background = self.import_background(path)

        # update the background path key to point to the file
        c = self.conn.cursor()
        c.execute('INSERT INTO zoom_kv VALUES (?,?,?)',
                        (ZoomConfig.background_path_key, background.path, 'ZoomChat'))

        # also update background data key to indicate whether the background is image or video
        c.execute('SELECT value FROM zoom_kv WHERE key = ?', (ZoomConfig.background_data_key,))
        row = c.fetchone()
        value = row[0].split(":")
        if background.type in ZoomConfig.background_types_image:
            value[4] = "1"
        elif background.type in ZoomConfig.background_types_video:
            value[4] = "2"
        else:
            raise Exception("unhandled type: " + str(background.type))
        value = ":".join(value)
        c.execute('UPDATE zoom_kv SET value = ? WHERE key = ?', (value, ZoomConfig.background_data_key))

        self.conn.commit()

    def delete_custom_backgrounds(self):
        c = self.conn.cursor()

        current_background = self.get_current_background_path()

        for row in c.execute('SELECT path, thumbPath FROM zoom_conf_video_background_a WHERE type in (?,?)', ZoomConfig.background_types_custom):
            path = row[0]
            thumb_path = row[1]
            if current_background and path == current_background:
                self.remove_current_background()
            if path.startswith(str(self.backgrounds_dir)):
                Path(path).unlink(missing_ok=True)
            if thumb_path and thumb_path.startswith(str(self.video_thumbs_dir)):
                Path(thumb_path).unlink(missing_ok=True)
        c.execute('DELETE FROM zoom_conf_video_background_a WHERE type in (?,?)', ZoomConfig.background_types_custom)
        self.conn.commit()

    def get_backgrounds(self):
        c = self.conn.cursor()
        backgrounds = []
        for row in c.execute('SELECT path, name, type, customIndex, thumbPath FROM zoom_conf_video_background_a WHERE type in (?,?)', ZoomConfig.background_types_custom):
            path = row[0]
            name = row[1]
            type = row[2]
            custom_index = row[3]
            thumb_path = row[4]
            background = VirtualBackground(path=path, name=name, type=type, custom_index=custom_index, thumb_path=thumb_path)
            backgrounds.append(background)
        return backgrounds

    def close(self):
        self.conn.close()

    def __del__(self):
        self.conn.close()

def open():
    if platform.system() == "Darwin":
        data_dir = Path("~/Library/Application Support/zoom.us/data").expanduser()
    elif platform.system() == "Windows":
        data_dir = Path(os.getenv("APPDATA")) / "Zoom" / "data"
    else:
        raise Exception("unsupported system: " + platform.system())
    return ZoomConfig(data_dir)