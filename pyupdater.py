#!/bin/env python2

import urllib
import urllib2
import json
import os
import sys
import time
import shutil
import traceback

add_url = "http://example.com/add"
login_url = "http://example.com/login"

class SMS:
    def __init__(self, number, when, ctype, amount, category, desc):
        self.number = number
        self.ctype = ctype
        self.amt = amount
        self.category = category
        self.desc = desc
        self.when = when


def add(session_id, sms):
    urlencode = urllib.urlencode
    data = {
        "session_id" : session_id,
        "when" : sms.when,
        "category" : sms.category,
        "amt" : sms.amt,
        "type" : sms.ctype,
        "mobile" : sms.number,
        "desc" : sms.desc
    }
    print "Going to Add ..."
    print "Data : " + repr(data)
    encoded_data = urlencode(data)
    url = add_url + "?" + encoded_data

    print "Requesting to URL : %s" % url
    response = urllib2.urlopen(url)

    print "Got response from URL : %s" % response.geturl()
    if url != response.geturl():
        print "Invalid session_id or session expired."
        raise InvalidSessionError("Invalid session_id or session expired.")

    json_data = response.read()

    try:
        response_data = json.loads(json_data)
    except ValueError as e:
        print "Error parsing response data as JSON. %s" % str(e)
        raise Exception("Error parsing response data as JSON. %s" % str(e))
    else:
        try:
            if response_data["status"] != '0':
                print "Failed to add. Error : %s" % response_data['desc']
                raise Exception("Failed to add. Error : %s" % response_data['desc'])
            else:
                print "Added successfully"
        except KeyError as e:
            print "Invalid data returned. Data : %s" % repr(response_data)
            raise Exception("Invalid data returned. Data : %s" % repr(response_data))


def login(user, password):
    urlencode = urllib.urlencode
    data = {
        "email" : user,
        "password" : password
    }
    print "Trying to login as <%s>" % user
    encoded_data = urlencode(data)
    url = login_url + "?" + encoded_data

    print "Requesting to URL : %s" % url
    response = urllib2.urlopen(url)

    json_data = response.read()

    try:
        response_data = json.loads(json_data)
    except ValueError as e:
        print "Error parsing response data as JSON. %s" % str(e)
        raise Exception("Error parsing response data as JSON. %s" % str(e))
    else:
        try:
            if response_data["status"] != '0':
                print "Failed to login. Error : %s" % response_data['desc']
                raise Exception("Failed to login. Error : %s" % response_data['desc'])
            else:
                print "Login successfully. session_id=%s" % response_data['session_id']
                return response_data['session_id']
        except KeyError as e:
            print "Error : %s" % e
            print "Invalid data " \
                  "returned. Data : %s" % repr(response_data)
            raise Exception("Invalid data " \
                            "returned. Data : %s" % repr(response_data))


class InvalidSMSError(Exception):
    pass

class InvalidSessionError(Exception):
    pass

def parse_sms(path, filename):
    filepath = path + "/" + filename
    if not os.access(filepath, os.R_OK):
        raise Exception("No access to the specified path.")

    if len(filename) < 23:
        raise InvalidSMSError("Invalid file name for sms")

    when = filename[-23:-13]

    with open(filepath) as f:
        fdata = f.read()

    fdata = fdata.split('\n')

    if len(fdata) < 4:
        print "Data read : %s " % repr(fdata)
        raise InvalidSMSError("Invalid data format in file.")

    number = fdata[0]
    amount = fdata[1].lower()
    category = fdata[2]
    desc = "\n".join(fdata[3 :])

    if (not number.startswith("+91")) or len(number) != 13:
        raise InvalidSMSError("Invalid mobile number : %s" % number)
    if amount.startswith("in "):
        ctype = 'income'
    elif amount.startswith("ex "):
        ctype = 'expense'
    else:
        raise InvalidSMSError("Invalid amount : %s" % amount)

    try:
        amount = float(amount[3: ])
    except ValueError:
        raise InvalidSMSError("Invalid amount : %s" % amount)

    return SMS(number, when, ctype, amount, category, desc)

def login_with_exception_handled(user, password):
    while True:
        try:
            session_id = login(user, password)
            print "Login successful"
            return session_id
        except urllib2.URLERROR:
            print "Network error. Unable to login..."
            print "Sleeping for 120 seconds"
            time.sleep(120)
            print "Retrying..."

if __name__ == '__main__':
    logfile = open("/content/SMS/MyExpenseSMS.log", "w")
    sys.stdout = logfile
    sys.stderr = logfile
    print "Starting the MyExpenseSMS service ..."
    user = 'root'
    password = '******'
    session_id = login_with_exception_handled(user, password)

    if not os.access('/content/SMS/success', os.F_OK):
        os.mkdir('/content/SMS/success')

    if not os.access('/content/SMS/invalid', os.F_OK):
        os.mkdir('/content/SMS/invalid')


    while True:
        for smsfile in os.listdir('/content/SMS/inbox'):
            try:
                sms = parse_sms('/content/SMS/inbox/', smsfile)
            except InvalidSMSError:
                print traceback.format_exc()
                shutil.move('/content/SMS/inbox/' + smsfile, '/content/SMS/invalid')
            else:
                try:
                    add(session_id, sms)
                    shutil.move('/content/SMS/inbox/' + smsfile, '/content/SMS/success')
                except InvalidSessionError:
                    session_id = login_with_exception_handled(user, password)
                except Exception as e:
                    print traceback.format_exc()
        print "Sleeping for 30 sec"
        sys.stdout.flush()
        time.sleep(30)







            
