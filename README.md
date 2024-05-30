# vcv2cvvc

### 概要
oto.ini変換用スクリプト

連続音形式のoto.iniファイルをCVVC形式に変換します。

```
> python .\vcv2cvvc.py -h
usage: vcv2cvvc.py [-h] [-o OUTPUT] [-s SETTING] [-n] [--limit LIMIT] [--suffix SUFFIX] [--cvvc-only] input

positional arguments:
  input                 Specify the conversion source oto.ini file.

options:
  -h, --help            show this help message and exit
  -o OUTPUT             Specify the conversion destination oto.ini file name. default='oto_cvvc.ini'
  -s SETTING            Specify the configuration file to be used for conversion. The default value is 
                        'setting.csv' which is the same location as the execution directory.
  -n                    Specify when assigning consecutive numbers to duplicate aliases.
  --limit LIMIT, -l LIMIT
                        Set the upper limit value for sequential numbers.
  --suffix SUFFIX       Set the suffix. It will not be given if the option is omitted.
  --cvvc-only           If --cvvc-only is set, vcv phonemes will not be output.
```

使用例

```
> python .\vcv2cvvc.py -o oto_cvvc.ini -n --limit 2 .\oto.ini 
```

* -o: 出力ファイルのパス（既にファイルが存在する場合は上書きされます）
* -n: 変換後に重複したエイリアスに連番を付与する場合に指定します。
* --limit: 重複エイリアスの上限値を指定します。--limitを指定しない場合は、上限なしで動作します。
* input: 入力ファイルのパス

変換後のファイルは、vcv2cvvc.pyと同じパスに出力されます。
すでに同名のファイルが存在する場合は上書きされます。


### 動作確認環境
* windows11
* python3.12.0