# encoding:utf-8

import logging
import re
import sys
import os
import argparse

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.WARN)

fh = logging.FileHandler("log.txt", mode='a', encoding="utf-8", delay=False)
fh.setLevel(logging.WARN)
logformat = "%(asctime)s %(levelname)s [%(name)s]%(message)s"
formatter = logging.Formatter(logformat)
fh.setFormatter(formatter)
LOG.addHandler(fh)



def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Specify the conversion source oto.ini file.")
    parser.add_argument("-s", dest="setting", default="setting.csv", 
        help=("Specify the configuration file to be used for conversion. "
            "The default value is 'setting.ini' which is the same location as the execution directory."))
    args = parser.parse_args()


    if os.path.exists(args.setting):
        oc = OtoConverter(args.setting)
    else:
        LOG.error("setting file not exists: {}".format(args.setting))
        print("指定された設定ファイルが存在しません")
        sys.exit(1)

    do_convert(args, oc)

def do_convert(args, oc):

    with open(args.input, "r", encoding="sjis") as f:
        with open("oto_cvvc.ini", "w", encoding="sjis") as f_out:

            for line in f:
                wavfile, params = line.split("=")
                # エイリアス, オフセット, 子音部, ブランク, 先行発声, オーバーラップ
                alias, offset, cons, cutoff, pre, ovl = params.split(",")
                offset, cons, cutoff, pre, ovl = [float(val.strip()) for val in [offset, cons, cutoff, pre, ovl]]

                # 先頭の場合 -> そのまま出力する
                if is_head(alias):
                    f_out.write(line)
                    continue

                try:
                    v,cv = alias.split(" ")
                except ValueError:
                # 分割できない場合 -> そのまま出力する
                    f_out.write(line)
                    continue

                # v-cvのc部分取り出す
                c = oc.change_alias(cv)

                if c is None:
                    LOG.warning("変換できませんでした: {}".format(alias))
                    f_out.write(line)
                    continue

                elif c == " ":
                    vc = cv

                else:
                    vc="{} {}".format(v, c)

                vcl = oc.get_vclength(c)

                if (vcl[1]==-1 and vcl[2] == -1):
                    f_out.write(line)
                    
                    continue

                # 母音の場合 -> そのまま出力 + V
                if is_vowel(cv):
                    f_out.write(line)
                    
                else:
                    # VC
                    n_offset = round(offset - vcl[0])
                    n_pre = round(pre)
                    n_cons = n_pre
                    n_cutoff = round(-(n_pre + vcl[1]))
                    n_ovl = round(ovl)

                    out = set_oto_line(wavfile,vc,n_offset,n_cons,n_cutoff,n_pre,n_ovl)
                    f_out.write(out)

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
                f_out.write(out)


def is_head(alias):
    '''
    語頭音素かどうかを判定する
    '''

    return alias.startswith("-")


def is_vowel(str_):

    vowel = ["あ", "い", "う", "え", "お", "ん"]
    return str_ in vowel


def set_oto_line(wavfile,alias,offset,cons,cutoff,pre,ovl):

    return  "{}={},{},{},{},{},{}\n".format(wavfile, alias, offset, cons, cutoff, pre, ovl)


class OtoConverter(object):
    def __init__(self, setfile="setting.csv"):
        self.params = self.read_setting(setfile)

    def read_setting(self, setfile):

        params = {}
        with open(setfile, "r", encoding="sjis") as f:

            for line in f:

                c_alias, org_alias, p1, p2, p3, p4 = line.split("=")
                for oa in org_alias.split(","):
                    params[oa] = {"new_c": c_alias, "params": [int(tmp.strip()) for tmp in [p1, p2, p3, p4]]}
      
        return params

    def change_alias(self, s):        
        if self.params.get(s):
            return self.params.get(s).get("new_c")

        return None
    
    def get_vclength(self, s):
        
        if self.params.get(s):
            return  self.params.get(s).get("params")

        return [-1, -1, -1, -1]


if __name__ == "__main__":


    main()
