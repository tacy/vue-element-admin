# http://ame.primeton.com/default/ame_common/wxworktime/com.primeton.rdmgr.labor.input.rdlabordetailbiz.saveAllRdLaborDetails1.biz.ext

# {"insertEntities":[{"actHours":"1.0","userId":"0218","laborDetailId":"","laborDate":"2017-10-30","otwHours":"1.0","custid":"","projectId":2,"tasklist":"46","repContent":"航旅纵横监控bug处理","status":0,"isDaysOff":"0","tbly":"","omOrganization":{"orgid":1120}}]}

# {"insertEntities":[{"actHours":"8.0","userId":"0218","laborDetailId":"","laborDate":"2017-10-30","otwHours":0,"custid":"","projectId":2,"tasklist":"46","repContent":"航旅纵横监控bug处理","status":0,"isDaysOff":"0","tbly":"","omOrganization":{"orgid":"1120"}}]}

# {"insertEntities":[{"actHours":"8.0","userId":"0218","laborDetailId":"","laborDate":"2017-10-27","otwHours":0,"custid":"1926","projectId":1,"tasklist":"94","repContent":"servicemesh","status":0,"isDaysOff":"0","tbly":"","omOrganization":{"orgid":"2760"}}]}

#  http://ame.primeton.com/default/common/jsp/codeImage.jsp?name=verifyCode&imageHeight=21&length=4&type=number

#  http://ame.primeton.com/default/org.gocom.abframe.auth.LoginManager.verifyCode.biz.ext

# 'code=4463&password=Asd1228*()&flag=true'

from PIL import Image
import io
import requests

if __name__ == '__main__':
    session = requests.session()
    session.get('http://ame.primeton.com/default/sso.login?SSOLOGOUT=true')
    session.headers.update({
        'User-Agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
        'Content-Type':
        'application/x-www-form-urlencoded'
    })
    r = session.get(
        'http://ame.primeton.com/default/common/jsp/codeImage.jsp?name=verifyCode&imageHeight=21&length=4&type=number'
    )
    with io.BytesIO(r.content) as f:
        with Image.open(f) as img:
            # img.show()
            # img = Image.open(im)
            img.show()
    verifyCode = input('verify code:')
    # print(verifyCode)
    data = {'code': verifyCode, 'password': 'Asd12288', 'flag': 'true'}
    r = session.post(
        'http://ame.primeton.com/default/org.gocom.abframe.auth.LoginManager.verifyCode.biz.ext',
        data=data)
    print(r.content)
    data = {
        '_eosFlowAction': 'login',
        'loginPage': 'ame/login/login.jsp',
        'service': 'http://ame.primeton.com/default/ame/clipview/index.jsp',
        'username': '0218',
        'password': 'Asd12288',
        'verifyCode': verifyCode,
    }
    r = session.post(
        'http://ame.primeton.com/default/sso.login?SSOLOGOUT=true', data=data)
    # print(r.content)
    session.headers.update({'Content-Type': 'text/json'})
    # task = {
    #     "insertEntities": [
    #         {
    #             "actHours": "8.0",
    #             "userId": "0218",
    #             "laborDetailId": "",
    #             "laborDate": "2017-10-20",
    #             "otwHours": 0,
    #             "custid": "1926",
    #             "projectId": 1,
    #             "tasklist": "94",
    #             "repContent": "servicemesh",
    #             "status": 0,
    #             "isDaysOff": "0",
    #             "tbly": "",
    #             "omOrganization": {
    #                 "orgid": "2760"
    #             },
    #         },
    #     ],
    # }
    task = {
        "insertEntities": [
            {
                "actHours": "8.0",
                "userId": "0218",
                "laborDetailId": "",
                "laborDate": "2017-10-20",
                "otwHours": 0,
                "custid": "",
                "projectId": 2,
                "tasklist": "46",
                "repContent": "servicemesh",
                "status": 0,
                "isDaysOff": "0",
                "tbly": "",
                "omOrganization": {
                    "orgid": "1120"
                },
            },
        ],
    }
    record = {
        '2017-10-23': '航旅纵横bug处理',
        '2017-10-25': '航旅纵横bug处理',
        '2017-10-26': '航旅纵横bug处理',
    }
    for k, v in record.items():
        task['insertEntities'][0]['laborDate'] = k
        task['insertEntities'][0]['repContent'] = v
        r = session.post(
            'http://ame.primeton.com/default/ame_common/wxworktime/com.primeton.rdmgr.labor.input.rdlabordetailbiz.saveAllRdLaborDetails1.biz.ext',
            json=task,
            allow_redirects=True)
