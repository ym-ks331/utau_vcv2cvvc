# encoding:utf-8

import logging
import re
import sys
import os
import argparse
import csv
import collections

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARN)

fh = logging.FileHandler("log.txt", mode='w', encoding="utf-8", delay=False)
fh.setLevel(logging.WARN)
logformat = "%(asctime)s %(levelname)s [%(name)s]%(message)s"
formatter = logging.Formatter(logformat)
fh.setFormatter(formatter)
LOG.addHandler(fh)


class GetParamsError(Exception):
    pass


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Specify the conversion source oto.ini file.")
    parser.add_argument("-o", dest="output", default="oto_cvvc.ini",
                        help="Specify the conversion destination oto.ini file name. default='oto_cvvc.ini'")
    parser.add_argument("-s", dest="setting", default="setting.csv", 
        help=("Specify the configuration file to be used for conversion. "
            "The default value is 'setting.csv' which is the same location as the execution directory."))
    parser.add_argument("-n", dest="setnum", action="store_true",
        help=("Specify when assigning consecutive numbers to duplicate aliases."))
    parser.add_argument("--limit", "-l", dest="limit", action="store", default=0, 
        help=("Set the upper limit value for sequential numbers."))
    parser.add_argument("--suffix", dest="suffix", action="store", default="", 
        help=("Set the suffix. It will not be given if the option is omitted."))
    args = parser.parse_args()


    if os.path.exists(args.setting):
        oc = OtoConverter(args.setting)
    else:
        LOG.error("setting file not exists: {}".format(args.setting))
        print("Specified configuration file does not exist.")
        sys.exit(1)
    
    ofw = OtoFileWriter(args.setnum, args.limit, args.suffix)

    convert_alias(args, oc, ofw)

def convert_alias(args, oc, ofw):

    try:
        with open(args.input, "r", encoding="sjis") as f:
            with open(args.output, "w", encoding="sjis") as f_out:

                for line in f:
                    wavfile, params = line.split("=")
                    # エイリアス, オフセット, 子音部, ブランク, 先行発声, オーバーラップ
                    alias, offset, cons, cutoff, pre, ovl = params.split(",")
                    offset, cons, cutoff, pre, ovl = [float(val.strip()) for val in [offset, cons, cutoff, pre, ovl]]

                    # 先頭の場合 -> そのまま出力する
                    if is_head(alias):
                        ofw.write_oto(f_out, line)
                        continue

                    try:
                        v,cv = alias.split(" ")
                    except ValueError:
                    # 分割できない場合 -> そのまま出力する
                        ofw.write_oto(f_out, line)
                        continue

                    # v-cvのc部分取り出す
                    c = oc.change_alias(cv)

                    if c is None:
                        LOG.warning("Could not convert: {}".format(alias))
                        ofw.write_oto(f_out, line)
                        continue

                    elif c == " ":
                        vc = cv

                    else:
                        vc="{} {}".format(v, c)

                    try:
                        vcl = oc.get_vclength(c)
                    except(GetParamsError): 
                        ofw.write_oto(f_out, line)                   
                        continue

                    # 母音の場合 -> そのまま出力 + V
                    if is_vowel(cv):
                        ofw.write_oto(f_out, line)
                        
                    else:
                        # VC
                        n_offset = round(offset - vcl[0])
                        n_pre = round(pre)
                        n_cons = n_pre
                        n_cutoff = round(-(n_pre + vcl[1]))
                        n_ovl = round(ovl)

                        out = set_oto_line(wavfile,vc,n_offset,n_cons,n_cutoff,n_pre,n_ovl)
                        ofw.write_oto(f_out, out)

                    cvl = oc.get_vclength(cv)
                    
                    # CV
                    n_offset = round(offset + pre - cvl[2])
                    left = round(n_offset - offset)
                    n_cons = round(cons-left) 
                    migi = round(cutoff)

                    if migi < 0:
                        n_cutoff = round(migi + left)
                    else:
                        n_cutoff = (cutoff) - left / 2
                    
                    n_pre = round(pre - left)
                    n_ovl = round(cvl[3])
                    
                    out = set_oto_line(wavfile,cv,n_offset,n_cons,n_cutoff,n_pre,n_ovl)
                    ofw.write_oto(f_out, out)

    except(FileNotFoundError):
        errmes="Specified file does not exist.: {}".format(args.input)
        print(errmes)
        LOG.exception(errmes)


class OtoFileWriter(object):

    def __init__(self, setnum=False, limit=0, suffix=""):
        self.setnum = setnum
        self.limit = int(limit)
        self.alias_dict = collections.defaultdict(int)
        self.suffix = suffix

    def write_oto(self, f_out, line):

        if not self.setnum:
            f_out.write(line)
            return

        wavfile, params = line.split("=")
        alias, params_ = params.split(",", 1)
        self.alias_dict[alias] += 1
        
        if self.alias_dict[alias] == 1:
            line = f"{wavfile}={alias}{self.suffix},{params_}"
        elif self.limit and self.alias_dict[alias] > self.limit:
            return 
        else:
            line = f"{wavfile}={alias}{self.suffix}{self.alias_dict[alias]},{params_}"

        f_out.write(line)


def is_head(alias):
    '''
    語頭音素かどうかを判定する
    '''
    return alias.startswith("-")


def is_vowel(str_):
    vowel = ["あ", "い", "う", "え", "お", "ん"]
    return str_ in vowel


def set_oto_line(wavfile,alias,offset,cons,cutoff,pre,ovl):
    return  f"{wavfile}={alias},{offset},{cons},{cutoff},{pre},{ovl}\n"


class OtoConverter(object):
    def __init__(self, setfile="setting.csv"):
        self.params = self.read_setting(setfile)
        
    def read_setting(self, setfile):

        f_params = ["p1", "p2", "p3", "p4"]
        fields = ["c_alias"] + f_params

        params = {}
        with open(setfile, "r", encoding="sjis") as f:

            settings = csv.DictReader(f, fieldnames=fields, restkey="org_alias")

            for setting in settings:
                for oa in setting["org_alias"]:
                    if oa == "":
                        continue
                    params[oa] = {"new_c": setting["c_alias"]}
                    for f_p in f_params:
                        params[oa][f_p] = int(setting[f_p].strip())

        return params

    def change_alias(self, s):        
        if self.params.get(s):
            return self.params.get(s).get("new_c")

        return None
    
    def get_vclength(self, s):
        
        if self.params.get(s):
            return  [self.params[s]["p1"], self.params[s]["p2"], self.params[s]["p3"], self.params[s]["p4"]]
        else:
            raise GetParamsError("aaa")


if __name__ == "__main__":
    main()
