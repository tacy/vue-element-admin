import requests


class JapanEmsAPI():
    def __init__(self, session, user, password):
        self.urltpl = 'https://www.int-mypage.post.japanpost.jp/mypage/'
        self.user = user
        self.password = password
        self.sess = requests.Session()

    def login(self):
        url = self.urltpl + 'M010000.do'
        payload = {
            'method:login': '',
            'request_locale': 'zh',
            'localeSel': 'zh',
            'loginBean.id': self.user,
            'loginBean.pw': self.password,
        }
        self.sess.post(
