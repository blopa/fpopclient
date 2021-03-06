import json
import base64
import datetime
import requests
import sys


class FreedomPop:
    refreshToken = None
    token = None
    tokenExpireTimestamp = None
    accessToken = None

    _apiClient = sys.argv[1]  # 3726328870
    _apiSecret = sys.argv[2]  # pNp6TIgVm4viVadoyoUdxbsrfmiBwudN
    endPoint = "https://api.freedompop.com"

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def _updateToken(self, params):
        url = self.endPoint + "/auth/token"
        headers = dict(Authorization = "Basic %s" % base64.encodestring("%s:%s" % (self._apiClient, self._apiSecret)).replace("\n", ""))
        buffer = requests.post(url, params=params, headers=headers, data="").content
        print buffer
        data = json.loads(buffer)
        self.accessToken = data["access_token"]
        self.refreshToken = data["refresh_token"]
        self.tokenExpireTimestamp = datetime.datetime.now() + datetime.timedelta(seconds = data["expires_in"])

        return True

    def _getAccessToken(self):
        params = dict(username = self.username, password = self.password, grant_type = "password")
        return self._updateToken(params)

    def _refreshAccessToken(self):
        params = dict(refresh_token = self.refreshToken, grant_type = "refresh_token")
        return self._updateToken(params)

    def initToken(self):
        if self.refreshToken is None:
            return self._getAccessToken()
        elif self.tokenExpireTimestamp < datetime.datetime.now():
            return self._refreshAccessToken()
        return True

    def _getBasic(self, command):
        if not self.initToken():
            return {}
        params = dict(accessToken = self.accessToken)
        url = "%s/%s" % (self.endPoint, command)
        buffer = requests.get(url, params=params).content
        return json.loads(buffer)

    def getPhoneNumbers(self, qtd):
        return self._getBasic("phone/getnumbers/" + qtd)

    def getAccountInfo(self):
        return self._getBasic("phone/account/info")

    def getSMS(self, startDate, endDate, includeDeleted, includeRead, includeOutgoing):  # TODO
        if not self.initToken():
            return {}
        params = dict(accessToken=self.accessToken, startDate=startDate, endDate=endDate, includeDeleted=str(includeDeleted).lower(), includeRead=str(includeRead).lower(), includeOutgoing=str(includeOutgoing).lower())
        url = self.endPoint + '/phone/listsms/'
        req = requests.get(url, params=params)
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            return False

    def getSMSBalance(self):
        usage = self.getUsage()
        if not usage:
            return False
        info = self.getAccountInfo()
        if not info:
            return False
        sms = self.getSMS(usage['startTime'], '', False, True, True)  # get sms including outgoing
        if not sms:
            return False

        base = info['voiceplan']['baseSMS']
        count = 0
        details = {}
        for t in sms['messages']:
            if t['from'] == str(info['phoneNumber']):  # count sent sms
                count += 1

        details['phoneNumber'] = str(info['phoneNumber'])
        details['startTime'] = str(usage['startTime'])
        details['planName'] = str(info['voiceplan']['name'])
        details['description'] = str(info['voiceplan']['description'])
        details['baseSMS'] = str(info['voiceplan']['baseSMS'])
        details['balanceSMS'] = str(int(base) - count)

        return details

    def getAllSMS(self):
        return self._getBasic("/phone/listsms")

    def getUsage(self):
        return self._getBasic("user/usage")

    def getInfo(self):
        return self._getBasic("user/info")

    def getPlan(self, planId = None):
        if planId is None:
            return self._getBasic("plan")
        else:
            return self._getBasic("plan/%s" % planId)

    def getPlans(self):
        return self._getBasic("plans")

    def getService(self, serviceId = None):
        if serviceId is None:
            return self._getBasic("service")
        else:
            return self._getBasic("service/%s" % serviceId)

    def getServices(self):
        return self._getBasic("services")

    def getContacts(self):
        return self._getBasic("contacts")

    def getFriends(self):
        return self._getBasic("friends")

    def sendSMS(self, to_numbers, message_body):  # TODO
        if not self.initToken():
            return {}
        url = self.endPoint + '/phone/sendsms/?accessToken=' + self.accessToken + '&to_numbers=' + to_numbers + '&message_body=' + message_body
        files = {'media_file': (None, 'none')}
        req = requests.post(url, files=files)
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            return False

    def setAsRead(self, message_id):  # TODO
        if not self.initToken():
            return {}
        params = dict(accessToken=self.accessToken, messageIds=message_id)
        url = self.endPoint + '/phone/sms/read/'
        return requests.put(url, params=params)

    def printMyInfo(self):
        usage = self.getUsage()
        inMB = 1024 * 1024
        endTime = datetime.datetime.fromtimestamp(usage["endTime"] / 1000)
        delta = endTime - datetime.datetime.now()
        print "Data used: %0.2f%% (%0.2f MB of %0.2f MB) Time until quota reset: %d days %d hours (%s)" % (usage["percentUsed"] * 100, usage["planLimitUsed"] / inMB, usage["totalLimit"] / inMB, delta.days, delta.seconds / 3600, endTime )


def run(username, password):
    fp = FreedomPop(username, password)
    fp.printMyInfo()
    """
    Full list of methods:
    fp.getUsage()       # get the data usage, begin/end quota period, quota MB bonuses.
    fp.getPlan()        # get current plan
    fp.getPlans()       # list of available plans
    fp.getService()     # get current subscribed service
    fp.getServices()    # list of available services
    fp.getInfo()        # get the account's first/last name, last login time, email address
    fp.getFriends()     # list of people friended this account
    fp.Contacts()       # I'm not sure what this for
    # there are some other API that can update/write to your account that I reluctant to expose it here...
    
    """

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print "Usage: python api.py 3726328870 pNp6TIgVm4viVadoyoUdxbsrfmiBwudN <username> <password>"
        sys.exit()

    run(sys.argv[3], sys.argv[4])

