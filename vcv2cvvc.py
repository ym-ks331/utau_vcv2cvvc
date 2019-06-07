# encoding:utf-8

import logging
import re

LOG = logging.getLogger()
LOG.setLevel(logging.WARN)

fh = logging.FileHandler("log.txt", mode='a', encoding="utf-8", delay=False)
fh.setLevel(logging.WARN)
logformat = "%(asctime)s %(levelname)s [%(name)s]%(message)s"
formatter = logging.Formatter(logformat)
fh.setFormatter(formatter)
LOG.addHandler(fh)

def main():

    oc = OtoConverter()

    with open("oto_vcv.ini", "r", encoding="sjis") as f:
        with open("newoto.ini", "w", encoding="sjis") as f_out:

            for line in f:
                wavfile, params = line.split("=")
                # エイリアス, オフセット, 子音部, ブランク, 先行発声, オーバーラップ
                alias, offset, cons, blank, pre, ovl = params.split(",")
                offset, cons, blank, pre, ovl = [float(val.strip()) for val in [offset, cons, blank, pre, ovl]]

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

                if c == "nai":
                    LOG.warning("変換できませんでした: {}".format(alias))
                    f_out.write(line)
                    continue

                if c == " ":
                    vc = cv
                else:
                    vc="{} {}".format(v, c)

                vcl = oc.get_vclength(c)

                if (vcl[1]==-1 and vcl[2] == -1):
                    f_out.write(line)
                    continue
                # 母音の場合 -> そのまま出力 + V
                if is_vowel(vc):
                    f_out.write(line)
                    
                else:
                    # VC
                    n_offset = round(offset - vcl[0])
                    n_pre = round(pre)
                    n_cons = n_pre
                    n_blank = round(-(n_pre + vcl[1]))
                    n_ovl = round(ovl)

                    out_ = set_oto_line(wavfile,vc,n_offset,n_cons,n_blank,n_pre,n_ovl)
                    f_out.write(out_)

            
                CV = alias.split(" ")[1]
                cvl = oc.get_vclength(CV)
                
                # CV
                n_offset = round(offset + pre - cvl[2])
                left = round( n_offset - offset)
                n_cons = round(cons-left) 
                migi = round(blank)
                n_blank = (0.0)

                if migi < (0.0):
                    n_blank = round(migi + left)
                else:
                    n_blank = (blank) - left / 2
                
                n_pre = round((pre) - left)
                n_ovl = round(cvl[3])
                
                out_ = set_oto_line(wavfile,CV,n_offset,n_cons,n_blank,n_pre,n_ovl)
                f_out.write(out_)



def is_head(alias):
    '''
    語頭音素かどうかを判定する
    '''

    return alias.startswith("-")

def is_vowel(str_):

    vowel = ["あ", "い", "う", "え", "お", "ん"]
    return str_ in vowel

def set_oto_line(wavfile,CV,n_offset,n_cons,n_blank,n_pre,n_ovl):

    return  "{}={},{},{},{},{},{}\n".format(wavfile,CV,n_offset,n_cons,n_blank,n_pre,n_ovl)


class OtoConverter(object):
    def __init__(self, setfile="setting.csv"):
        self.params = self.read_setting(setfile)

    def read_setting(self, setfile):

        params = {}
        with open(setfile, "r", encoding="utf-8") as f:

            for line in f:

                c_alias, old_alias, p1, p2, p3, p4 = line.split("=")
                for oa in old_alias.split(","):
                    params[oa] = {"new_c": c_alias, "params": [int(tmp.strip()) for tmp in [p1, p2, p3, p4]]}

      
        return params

    def change_alias(self, s):        
        if self.params.get(s):
            return  self.params.get(s).get("new_c")

        return "nai"
    
    def get_vclength(self, s):
        
        if self.params.get(s):
            return  self.params.get(s).get("params")

        return [-1, -1, -1, -1]


 

if __name__ == "__main__":
    main()