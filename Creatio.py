# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org requests
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pickle
import json
import sys
import argparse

out = sys.stdout
outto = None

#---------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument("method", type=str, help="Method name (get|metadata)")
parser.add_argument("collection", type=str, help="Collection name or comma delimited list")
parser.add_argument("-cf", "--cookiefile", action="store", dest="cookiefile", type=str, help="Path to cookie file")
# file or console
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-c", "--console", action="store_true", help="Out result to console")
group.add_argument("-fp", "--filepath", action="store", dest="filepath", type=str, help="Out result to file in path")
try:
	args = parser.parse_args()
except:
	sys.exit(0)
if args.console:
	outto = "console"
else:
	outto = "file"
	filepath = args.filepath

method = args.method.lower()
collection = "" if args.collection.lower() == "none" else args.collection
cookiefile = args.cookiefile
#---------------------------------------------------

verify_flag = False
sys.tracebacklimit = 0
if (verify_flag == False):
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#---------------------------------------------------
url_auth = "https://pre-ervez.terrasoft.ru/ServiceModel/AuthService.svc/Login"
url_coll = "https://pre-ervez.terrasoft.ru/0/odata"
username = "peter"
userpassword = "Peter@1234"
#---------------------------------------------------

headers = {
	"Accept": "application/json",
	"Content-Type": "application/json; charset=utf-8",
	"ForceUseSession": "true"
}

error = None
retry_cnt = 2

#---------------------------------------------------
class Exception(object):
	Helplink = None
	Innerexception = None
	Message = None
	Stacktrace = None
	Type = None
	def __init__(self, dictionary):
		for key in dictionary:
			k = key.lower().capitalize()
			if k in {"Helplink"}:
				setattr(self, k, dictionary[key])
class Error(object):
	Code = None
	Message = None
	Exception = None
	Passwordchangeurl = None
	Redirecturl = None
	def __init__(self, dictionary):
		for key in dictionary:
			k = key.lower().capitalize()
			if k in {"Exception1"}:
				if not dictionary[k] is None:
					setattr(self, k, Exception(dictionary[key]))    
			elif k in {"Code","Message","Passwordchangeurl","Redirecturl"}:
				setattr(self, k, dictionary[key])

#---------------------------------------------------
def save_cookies(requests_cookiejar, filename):
	with open(filename, 'wb') as f:
		pickle.dump(requests_cookiejar, f)
#---------------------------------------------------
def load_cookies(filename):
	with open(filename, 'rb') as f:
		return pickle.load(f)
#---------------------------------------------------
def auth() -> bool:
	global error
	global headers
	global cookiepath, cookiefilename
	ret = True
	payload = "{\"UserName\":\"" + username + "\",\"UserPassword\":\"" + userpassword + "\"}"
	response = requests.request("POST", url_auth, headers=headers, data=payload, verify=False)
	error = Error(json.loads(response.text))
	if (error.Code == 0):
		save_cookies(response.cookies, cookiefile)
	else:
		ret = False
	return ret

#---------------------------------------------------
def get(collection):
	global error	
	global retry_cnt
	global cookiepath, cookiefilename

	retry = True
	retry_c = 0

	s = ""

	while (retry):
		retry_c = retry_c + 1
		if retry_c >= retry_cnt:
			retry = False
		try:
			response = requests.request("GET", url_coll+"/"+collection, headers=headers, cookies=load_cookies(cookiefile), verify=verify_flag)

			if "@odata.context" in response.text:
				retry = False
			elif "File or directory not found" in response.text:
				payload = {
					"Code": 1,
					"Message": "File or directory not found"
					}
				error = Error(payload)
				retry = False
			else:
				auth()
		except:
			# if file with cookies not found
			auth()
		if not retry:
			break
	
	# check error 1
	if error is not None:
		if error.Code != 0:
			status = False
			return json.dumps(error.__dict__)

	js = json.loads(response.text)

	# check error 2
	if "@odata.context" not in response.text:
		if js.get("error") != None:
			payload = {
				"Code": 1,
				"Message": json.dumps(js["error"])
				}			
		else:
			payload = {
				"Code": 1,
				"Message": response.text
				}
		error = Error(payload)
		return json.dumps(error.__dict__)

	status = True
	if status:
		collection = 'metadata' if collection == "" else collection

		if len(js["value"]) > 0:
			# get keys
			js_v = json.loads(json.dumps(js["value"][0]))

			s = "[{\"values\":["

			for j in js["value"]:
				s = s + "{"

				s = s + "\"collection\":\"" + collection + "\","		
				if (collection != "metadata"):
					s = s + "\"id\":\"" + j["Id"] +"\","
					s = s + "\"CreatedOn\":\"" + j["CreatedOn"] +"\","
					s = s + "\"ModifiedOn\":\"" + j["ModifiedOn"] +"\","

				s = s + "\"data\":\"{"
				for key, value in js_v.items():
					if key not in ["Id", "CreatedOn", "ModifiedOn"]:
						s = s + "\\\"" + key + "\\\":\\\"" + str(j[key]) + "\\\","
				s = s[:-1]
				s = s + "}\"},"
		
			s = s[:-1]
			s =	s + "]}]"

	return s

#---------------------------------------------------

if method == "get":
	coll_list = collection.split(",")
	for c in coll_list:
		s = get(c)
		if outto == "console":
			out.write(s)
		else:
			with open(f"{filepath}/{c}.json", 'wt', encoding='utf-8') as f:
				f.write(s)
elif method == "metadata" and collection != "ALL":
	s = get("")
	if outto == "console":
		out.write(s)
	else:
		with open(f"{filepath}/metadata.json", 'wt', encoding='utf-8') as f:
			f.write(s)
elif method == "metadata" and collection == "ALL":
	s = get("")
	j = json.loads(s)
	for k in j:
		v = k["values"]
		for d in v:
			dj = json.loads(d["data"])
			print(name)
			if name not in ("VwSysSchemaInfo"):
				s = get(name)
				with open(f"{filepath}/{name}.json", 'wt', encoding='utf-8') as f:
					f.write(s)

