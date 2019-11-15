import requests
import hashlib
import random
import time
from urllib.parse import quote_plus
from googletrans import Translator as GoogTranslator
from datetime import datetime, timedelta
from functools import wraps


__all__ = ['throttle', 'Translator', 'BaiduTranslator', 'TencentTranslator', 'GoogleTranslator']


class throttle(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.
    To create a function that cannot be called more than once a minute:
        @throttle(minutes=1)
        def my_fun():
            pass
    """

    def __init__(self, seconds=1, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_since_last_call = now - self.time_of_last_call

            if time_since_last_call > self.throttle_period:
                self.time_of_last_call = now
                return fn(*args, **kwargs)
            else:
                time.sleep(max((self.throttle_period - time_since_last_call).total_seconds(), 0.1))
                self.time_of_last_call = datetime.now()
                return fn(*args, **kwargs)

        return wrapper


class Translator(object):
    def translate(self, text, dest, src):
        """ return translated text or raise Exception """
        raise NotImplementedError


class GoogleTranslator(object):
    def __init__(self):
        self.translator = GoogTranslator()

    def translate(self, text, dest, src='auto'):
        return self.translator.translate(text, dest=dest, src=src).text


class BaiduTranslator(object):
    def __init__(self, appid, secret):
        self.appid = appid
        self.secret = secret
        self.url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

    def get_sign(self, text, salt):
        sign = self.appid + text + str(salt) + self.secret
        m = hashlib.md5()
        m.update(sign.encode('utf8'))
        return m.hexdigest()

    def get_salt(self):
        return random.randint(32768, 65536)

    def translate(self, text, dest='en', src='auto'):
        if text is None or len(text.strip()) == 0:
            return ''
        salt = self.get_salt()
        sign = self.get_sign(text, salt)
        res = requests.get(self.url, params={
            'appid': self.appid,
            'q': text,
            'from': src,
            'to': dest,
            'salt': salt,
            'sign': sign
        })
        dat = res.json()
        if 'trans_result' in dat:
            ret = []
            for item in dat['trans_result']:
                ret.append(item['dst'])
            return '\n'.join(ret)
        raise Exception('trans_result field not found')


class TencentTranslator(Translator):
    def __init__(self, appid, secret):
        self.app_id = appid
        self.app_key = secret
        self.url_prefix = 'https://api.ai.qq.com/fcgi-bin/'
        self.url = ''
        self.data = {}

    def set_params(self, key, value):
        self.data[key] = value

    def clear_data(self):
        self.data = {}

    def invoke(self, params):
        res = requests.get(self.url, params)
        dat = res.json()
        return dat

    def gen_sign_str(self):
        uri_str = ''
        for key in sorted(self.data.keys()):
            if key == 'app_key':
                continue
            uri_str += "%s=%s&" % (key, quote_plus(str(self.data[key]), safe=''))
        # '~' character is not quoted by python quote function, need to manually replace
        uri_str = uri_str.replace('~', '%7E')
        sign_str = uri_str + 'app_key=' + self.data['app_key']

        hash_md5 = hashlib.md5(sign_str.encode('utf8'))
        return hash_md5.hexdigest().upper()

    def get_nlp_text_translate(self, text, source, target):
        self.url = self.url_prefix + 'nlp/nlp_texttranslate'
        self.clear_data()
        self.set_params('app_id', self.app_id)
        self.set_params('app_key', self.app_key)
        self.set_params('time_stamp', int(time.time()))
        self.set_params('nonce_str', int(time.time()))
        self.set_params('text', text)
        self.set_params('source', source)
        self.set_params('target', target)
        sign_str = self.gen_sign_str()
        self.set_params('sign', sign_str)
        return self.invoke(self.data)

    def translate(self, text, dest='en', src='auto'):
        text = text.strip()  # space prefix will cause sign error
        dat = self.get_nlp_text_translate(text, src, dest)
        if dat['ret'] != 0:
            raise Exception('api error, msg: %s' % dat['msg'])
        return dat['data']['target_text']
