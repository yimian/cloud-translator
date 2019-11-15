# cloud-translator

Use the same api to call the third party translator apis, such as google, tencent, baidu.

### Prerequisite

Python 3.7 or more latest version

### Installation

```shell
pip install cloud-translator
```

### Usage

The library support GoogleTranslator, TencentTranslator, BaiduTranslator, where GoogleTranslator depends on [py-googletrans](https://github.com/ssut/py-googletrans) which not needs appid and appkey, but is not stable and probably blocked by google.

TencentTranslator and BaiduTranslator are rewritted with reference to the offical demo script to support python 3.7 version

```python
from translator import *

# use google
translator = GoogleTranslator()
print(translator.translate('我是中国人', dest='en'))

# use baidu api
translator = BaiduTranslator(appid, appkey)
print(translator.translate('我是中国人', dest='en'))

# use tencent api
translator = TencentTranslator(appid, appkey)
print(translator.translate('我是中国人', dest='en'))

# throttle api call frequency.
translate_func = throttle(seconds=1)(translator.translate) # call api every second
for i in range(100):
  translate_func('我是中国人', dest='en')
```

