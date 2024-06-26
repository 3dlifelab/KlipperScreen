import logging
import re
import requests


class KlippyRest:
    def __init__(self, ip, port=7125, api_key=False):
        self.ip = ip
        self.port = port
        self.api_key = api_key
        self.status = ''

    @property
    def endpoint(self):
        protocol = "http"
        if int(self.port) in {443, 7130}:
            protocol = "https"
        return f"{protocol}://{self.ip}:{self.port}"

    def get_server_info(self):
        return self.send_request("server/info")

    def get_oneshot_token(self):
        r = self.send_request("access/oneshot_token")
        if r is False or 'result' not in r:
            return False
        return r['result']

    def get_printer_info(self):
        return self.send_request("printer/info")

    def get_gcode_help(self):
        return self.send_request("printer/gcode/help")

    def get_thumbnail_stream(self, thumbnail):
        return self.send_request(f"server/files/gcodes/{thumbnail}", json=False)

    def _do_request(self, method, request_method, data=None, json=None, json_response=True):
        url = f"{self.endpoint}/{method}"
        headers = {} if self.api_key is False else {"x-api-key": self.api_key}
        response_data = False
        try:
            callee = getattr(requests, request_method)
            response = callee(url, json=json, data=data, headers=headers, timeout=3)
            response.raise_for_status()
            if json_response:
                logging.debug(f"Sending request to {url}")
                response_data = response.json()
            else:
                response_data = response.content
        except requests.exceptions.HTTPError as h:
            self.status = self.format_status(h)
        except requests.exceptions.ConnectionError as c:
            self.status = self.format_status(c)
        except requests.exceptions.Timeout as t:
            self.status = self.format_status(t)
        except requests.exceptions.JSONDecodeError as j:
            self.status = self.format_status(j)
        except requests.exceptions.RequestException as r:
            self.status = self.format_status(r)
        except Exception as e:
            self.status = self.format_status(e)
        if response_data:
            self.status = ''
        else:
            logging.error(self.status.replace('\n', '>>'))
        return response_data

    def post_request(self, method, data=None, json=None, json_response=True):
        return self._do_request(method, "post", data, json, json_response)

    def send_request(self, method, json=True):
        return self._do_request(method, "get", json_response=json)

    @staticmethod
    def format_status(status):
        try:
            rep = {"HTTPConnectionPool": "", "/server/info ": "", "Caused by ": "", "(": "", ")": "",
                   ": ": "\n", "'": "", "`": "", "\"": ""}
            rep = {re.escape(k): v for k, v in rep.items()}
            pattern = re.compile("|".join(rep.keys()))
            status = pattern.sub(lambda m: rep[re.escape(m.group(0))], f"{status}").split("\n")
            return "\n".join(_ for _ in status if "urllib3" not in _ and _ != "")
        except TypeError or KeyError:
            return status
