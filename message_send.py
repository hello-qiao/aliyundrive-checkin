import requests
import json
import json
from typing import Optional, Union

class PushDeer:
    server = "https://api2.pushdeer.com"
    endpoint = "/message/push"
    pushkey = None

    def __init__(self, server: Optional[str] = None, pushkey: Optional[str] = None):
        if server:
            self.server = server
        if pushkey:
            self.pushkey = pushkey

    def _push(self, text: str, desp: Optional[str] = None, server: Optional[str] = None,
              pushkey: Optional[str] = None, text_type: Optional[str] = None, **kwargs):

        if not pushkey and not self.pushkey:
            raise ValueError("pushkey must be specified")

        res = self._send_push_request(desp, pushkey or self.pushkey, server or self.server, text, text_type, **kwargs)
        if res["content"]["result"]:
            result = json.loads(res["content"]["result"][0])
            if result["success"] == "ok":
                return True
            else:
                return False
        else:
            return False

    def _send_push_request(self, desp, key, server, text, type, **kwargs):
        return requests.get(server + self.endpoint, params={
            "pushkey": key,
            "text": text,
            "type": type,
            "desp": desp,
        }, **kwargs).json()

    def send_text(self, text: str, desp: Optional[str] = None, server: Optional[str] = None,
                  pushkey: Union[str, list, None] = None, **kwargs):
        """
        Any text are accepted when type is text.
        @param text: message : text
        @param desp: the second part of the message (optional)
        @param server: server base
        @param pushkey: pushDeer pushkey
        @return: success or not
        """
        return self._push(text=text, desp=desp, server=server, pushkey=pushkey, text_type='text', **kwargs)

    def send_markdown(self, text: str, desp: Optional[str] = None, server: Optional[str] = None,
                      pushkey: Union[str, list, None] = None, **kwargs):
        """
        Text in Markdown format are accepted when type is markdown.
        @param text: message : text in markdown
        @param desp: the second part of the message in markdown (optional)
        @param server: server base
        @param pushkey: pushDeer pushkey
        @return: success or not
        """
        return self._push(text=text, desp=desp, server=server, pushkey=pushkey, text_type='markdown', **kwargs)

    def send_image(self, image_src: str, desp: Optional[str] = None, server: Optional[str] = None,
                   pushkey: Union[str, list, None] = None, **kwargs):
        """
        Only image src are accepted by API now, when type is image.
        @param image_src: message : image URL
        @param desp: the second part of the message (optional)
        @param server: server base
        @param pushkey: pushDeer pushkey
        @return: success or not
        """
        return self._push(text=image_src, desp=desp, server=server, pushkey=pushkey, text_type='image', **kwargs)




class MessageSend:
    def __init__(self):
        self.sender = {}

        self.register("pushplus_token", self.pushplus)
        self.register("serverChan_token", self.serverChan)
        self.register("weCom_tokens", self.weCom)
        self.register("weCom_webhook", self.weCom_bot)
        self.register("bark_deviceKey", self.bark)
        self.register("feishu_deviceKey", self.feishu)

    def register(self, token_name, callback):
        assert token_name not in self.sender, "Register fails, the token name exists."
        self.sender[token_name] = callback

    def send_all(self, message_tokens, title, content):
        def check_valid_token(token):
            if isinstance(token, type(None)):
                return False
            if isinstance(token, str) and len(token) == 0:
                return False
            if isinstance(token, list) and (token.count(None) != 0 or token.count("") != 0):
                return False
            return True

        for token_key in message_tokens:
            token_value = message_tokens[token_key]
            if token_key in self.sender and check_valid_token(token_value):
                try:
                    ret = self.sender[token_key](token_value, title, content)
                except:
                    print(f"[Sender]Something wrong happened when handle {self.sender[token_key]}")

    def pushplus(self, token, title, content):
        assert type(token) == str, "Wrong type for pushplus token."
        content = content.replace("\n", "\n\n")
        payload = {
            'token': token,
            "title": title,
            "content": content,
            "channel": "wechat",
            "template": "markdown"
        }
        resp = requests.post("http://www.pushplus.plus/send", data=payload)
        resp_json = resp.json()
        if resp_json["code"] == 200:
            print(f"[Pushplus]Send message to Pushplus successfully.")
        if resp_json["code"] != 200:
            print(f"[Pushplus][Send Message Response]{resp.text}")
            return -1
        return 0

    def serverChan(self, sendkey, title, content):
        assert type(sendkey) == str, "Wrong type for serverChan token."
        content = content.replace("\n", "\n\n")
        payload = {
            "title": title,
            "desp": content,
        }
        # https://push.wudixiaolong.xyz/message/push?pushkey=PDU1TtzDLwF2Y7sCPSWGOYT3rp4fwbNKl6lu6&text=%E8%A6%81%E5%8F%91%E9%80%81%E7%9A%84%E5%86%85%E5%AE%B9
        pushdeer = PushDeer(server="https://push.wudixiaolong.xyz", pushkey="PDU1TtzDLwF2Y7sCPSWGOYT3rp4fwbNKl6lu6")
        pushdeer.send_text(title, desp=content)
        # resp = requests.post(f"https://sctapi.ftqq.com/{sendkey}.send", data=payload)
        # resp_json = resp.json()
        # if resp_json["code"] == 0:
        #     print(f"[ServerChan]Send message to ServerChan successfully.")
        # if resp_json["code"] != 0:
        #     print(f"[ServerChan][Send Message Response]{resp.text}")
        #     return -1
        return 0

    def weCom(self, tokens, title, content):
        proxy_url = None
        to_user = None
        tokens = tokens.split(",")
        if len(tokens) == 3:
            weCom_corpId, weCom_corpSecret, weCom_agentId = tokens
        elif len(tokens) == 4:
            weCom_corpId, weCom_corpSecret, weCom_agentId, to_user = tokens
        elif len(tokens) == 5:
            weCom_corpId, weCom_corpSecret, weCom_agentId, to_user, proxy_url = tokens
        else:
            return -1

        qy_url = proxy_url or "https://qyapi.weixin.qq.com"
        get_token_url = f"{qy_url}/cgi-bin/gettoken?corpid={weCom_corpId}&corpsecret={weCom_corpSecret}"
        resp = requests.get(get_token_url)
        resp_json = resp.json()
        if resp_json["errcode"] != 0:
            print(f"[WeCom][Get Token Response]{resp.text}")
        access_token = resp_json.get('access_token')
        if access_token is None or len(access_token) == 0:
            return -1
        send_msg_url = f'{qy_url}/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": to_user or "@all",
            "agentid": weCom_agentId,
            "msgtype": "news",
            "news": {
                "articles": [
                    {
                        "title": title,
                        "description": content,
                        "picurl": "https://raw.githubusercontent.com/libuke/aliyundrive-checkin/main/aliyunpan.jpg",
                        "url": ''
                    }
                ]
            },
            "duplicate_check_interval": 600
        }
        resp = requests.post(send_msg_url, data=json.dumps(data))
        resp_json = resp.json()
        if resp_json["errcode"] == 0:
            print(f"[WeCom]Send message to WeCom successfully.")
        if resp_json["errcode"] != 0:
            print(f"[WeCom][Send Message Response]{resp.text}")
            return -1
        return 0

    def weCom_bot(self, webhook, title, content):
        assert type(webhook) == str, "Wrong type for WeCom webhook token."
        assert "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?" in webhook, "Please use the whole webhook url."
        headers = {
            'Content-Type': "application/json"
        }
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }
        resp = requests.post(webhook, headers=headers, data=json.dumps(data))
        resp_json = resp.json()
        if resp_json["errcode"] == 0:
            print(f"[WeCom]Send message to WeCom successfully.")
        if resp_json["errcode"] != 0:
            print(f"[WeCom][Send Message Response]{resp.text}")
            return -1
        return 0

    def bark(self, device_key, title, content):
        assert type(device_key) == str, "Wrong type for bark token."

        url = "https://api.day.app/push"
        headers = {
            "content-type": "application/json",
            "charset": "utf-8"
        }
        data = {
            "title": title,
            "body": content,
            "device_key": device_key
        }

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp_json = resp.json()
        if resp_json["code"] == 200:
            print(f"[Bark]Send message to Bark successfully.")
        if resp_json["code"] != 200:
            print(f"[Bark][Send Message Response]{resp.text}")
            return -1
        return 0

    def feishu(self, device_key, title, content):
        assert type(device_key) == str, "Wrong type for feishu token."

        url = f'https://open.feishu.cn/open-apis/bot/v2/hook/{device_key}'
        headers = {
            "content-type": "application/json",
            "charset": "utf-8"
        }

        data = {"msg_type": "post", "content": {"post": {"zh_cn": {"title": title, "content": [[{"tag": "text", "text": content}]]}}}}

        resp = requests.post(url, headers=headers, json=data)
        resp_json = resp.json()
        if resp_json["code"] == 0:
            print(f"[Bark]Send message to Bark successfully.")
        if resp_json["code"] != 0:
            print(f"[Bark][Send Message Response]{resp.text}")
            return -1
        return 0
