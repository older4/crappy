from itertools import chain, takewhile
import base64
import re


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