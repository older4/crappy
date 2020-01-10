from itertools import chain, takewhile
import base64
import re
import glob
import os
import win32.win32api as win32api


def int_from_bytes(bytes_, byteorder):
    return int.from_bytes(bytes_, byteorder)


def int_to_bytes(n, length, order):
    return n.to_bytes(length, order)

# Inspired by https://stackoverflow.com/questions/30545497/python-line-split-between-two-delimeters


def get_ransom_data(path, name="GANDCRAB KEY"):
    with open(path, "r", encoding="utf-16") as f:
        f = map(str.rstrip, f)
        st, end = "---BEGIN %s---" % name, "---END %s---" % name
        out = "".join(chain.from_iterable(takewhile(lambda x: x != end, f)
                                          for line in f if line == st))
    return base64.b64decode(out)

def get_ransom_ver(path, name="GANDCRAB KEY"):
    with open(path, "r", encoding="utf-16") as f:
        ver_text = f.readline()

    ver = re.search("(\d|\.){1,}",ver_text).group()
    # Like 5.0.4 has two dot, so it is not float.
    # Convert 5.0.4 to 5.04
    tmp = re.findall(r"\.\d",ver)
    if(len(tmp)>1):
        ver = re.sub(r"\.\d$",tmp[-1].strip("."),ver)

    return float(ver)

def get_ransom_ext(threat_note_path):
    file_name = os.path.splitext(os.path.basename(threat_note_path))[0]
    return re.sub(r"-DECRYPT","",file_name).lower()

def get_logical_drives():
    drives = win32api.GetLogicalDriveStrings()
    drives = drives.split('\000')[:-1]
    tmp_list = drives
    # 有効なディスクかチェック
    for count, drive_letter in enumerate(tmp_list):
        try:
            win32api.GetDiskFreeSpaceEx(drive_letter)
        except:
            del drives[count]

    return drives

def scan_crypted_file(skip_root_folders="defalt",ext=None):
    drives = get_logical_drives()
    if(skip_root_folders == "defalt"):
        skip_root_folders = ["Windows","Program Files"]

    if(ext):
        ext = "/*." + ext
    else:
        ext = ""

    for drive in drives:
        for path in glob.iglob(drive+"*"):
            for skip in skip_root_folders:
                if(skip in path):
                    break
                
                if(skip == skip_root_folders[-1]):
                    for p in glob.iglob(path+"/**{}".format(ext),recursive=True):
                        if(os.path.isfile(p)):
                            yield p

