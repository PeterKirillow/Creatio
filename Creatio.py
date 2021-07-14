# pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org requests
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import pickle
import json
import sys
import argparse
from datetime import datetime

#---------------------------------------------------
domain = "pre-ervez.terrasoft.ru"
url_auth = "https://" + domain + "/ServiceModel/AuthService.svc/Login"
url_coll = "https://" + domain + "/0/odata"
username = "peter"
userpassword = "Peter@1234"
#---------------------------------------------------

out = sys.stdout
sys.tracebacklimit = 0
# disable insecure ssl verify
verify_flag = False
if (verify_flag == False):
	requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
outto = None
error = None
BPMCSRF = None

#---------------------------------------------------
# -cf d:/projects/git/creatio/creatio_cookie  -fp c:/tmp/json metadata none
# -cf d:/projects/git/creatio/creatio_cookie -c get Employee
# -cf d:/projects/git/creatio/creatio_cookie -c get Contact,Employee

# filter example - https://documenter.getpostman.com/view/10204500/SztHX5Qb?version=latest#c543848b-cbec-4d4c-9037-e0234b5b3b6c
# -cf d:/projects/git/creatio/creatio_cookie -fp c:/tmp/json get Contact -f "ModifiedOn gt 2021-06-13T00:00:00.00Z"

# create object - https://documenter.getpostman.com/view/10204500/SztHX5Qb?version=latest#837e4578-4a8c-4637-97d4-657079f12fe0
# -cf d:/projects/git/creatio/creatio_cookie -c post Contact -d "{'Name': 'New User', 'JobTitle': 'Developer', 'BirthDate': '1980-08-24T00:00:00Z'}"
# -cf d:/projects/git/creatio/creatio_cookie -c post Contact -d "{'Name': 'Новый пользователь', 'JobTitle': 'DДиректор', 'BirthDate': '1980-08-24T00:00:00Z'}"
# update object - https://documenter.getpostman.com/view/10204500/SztHX5Qb?version=latest#da518295-e1c8-4114-9f03-f5f236174986
# -cf d:/projects/git/creatio/creatio_cookie -c patch Contact(f78473be-7903-4b12-8172-013d9b8ebc26) -d "{'JobTitle': 'Simple Job', 'BirthDate': '1980-08-24T00:00:00Z'}"
# delete object - https://documenter.getpostman.com/view/10204500/SztHX5Qb?version=latest#364435a7-12ef-4924-83cf-ed9e74c23439
# -cf d:/projects/git/creatio/creatio_cookie -c delete Contact(a1efd326-507b-4519-9e58-3e0fcff84389)
#---------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("method", type=str, help="Method name (get|post|patch|delete|metadata)")
parser.add_argument("collection", type=str, help="Collection name or comma delimited list")
parser.add_argument("-cf", "--cookiefile", action="store", dest="cookiefile", type=str, required=True, help="Path to cookie file")
# filter
parser.add_argument("-f", "--filter", action="store", dest="filter", type=str, help="Filter expression")
# data-raw
parser.add_argument("-d", "--data", action="store", dest="dataraw", type=str, help="Data in json format")
# output to file or console
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

method = args.method.upper()
collection = "" if args.collection.lower() == "none" else args.collection
cookiefile = args.cookiefile
filter = "" if args.filter is None else "?$filter=" + args.filter
if args.dataraw is None:
	dataraw = ""
else:
	dataraw = args.dataraw.replace("'","\"")

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
			if k in {"Helplink","InnerException","Message","StackTrace","Type"}:
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
			if k in {"Exception"}:
				if not dictionary[k] is None:
					setattr(self, k, Exception(dictionary[key]))    
			elif k in {"Code","Message","Passwordchangeurl","Redirecturl"}:
				setattr(self, k, dictionary[key])
	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__, sort_keys=False, indent=4)

#---------------------------------------------------
def save_cookies(requests_cookiejar, filename):
	with open(filename, 'wb') as f:
		pickle.dump(requests_cookiejar, f)

#---------------------------------------------------
def load_cookies(filename):
	try:
		with open(filename, 'rb') as f:
			return pickle.load(f)
	except:
		return None

#---------------------------------------------------
def auth() -> bool:
	global error
	global cookiefile
	ret = True
	headers = {
		"Accept": "application/json",
		"Content-Type": "application/json; charset=utf-8",
		"ForceUseSession": "true"
		}
	payload = "{\"UserName\":\"" + username + "\",\"UserPassword\":\"" + userpassword + "\"}"
	response = requests.request("POST", url_auth, headers=headers, data=payload, verify=False)
	if response.status_code != 200:
		error = Error({"Code": 1, "Message": str(response.status_code) + ": " + response.reason})
		ret = False
	else:
		error = Error(json.loads(response.text))
		if (error.Code == 0):
			save_cookies(response.cookies, cookiefile)
		else:
			ret = False
	return ret

#---------------------------------------------------
def call(method, collection):
	global error	
	global cookiefile, dataraw

	retry = True
	retry_c = 0

	s = ""
	response = None

	while (retry):
		retry_c = retry_c + 1
		if retry_c >= 2:
			retry = False
		try:
			c = load_cookies(cookiefile)
			BPMCSRF = c.get_dict(domain=domain)["BPMCSRF"]
			headers = {
				"Accept": "application/json",
				"Content-Type": "application/json; charset=utf-8",
				"ForceUseSession": "true",
				"BPMCSRF" : BPMCSRF
				}

			if method == "GET":
				response = requests.get(url_coll+"/"+collection+filter, headers=headers, cookies=c, verify=verify_flag)
			elif method == "POST":
				response = requests.post(url_coll+"/"+collection, headers=headers, data=dataraw, cookies=c, verify=verify_flag)
			elif method in {"PATCH","DELETE"}:
				response = requests.request(method, url_coll+"/"+collection, headers=headers, data=dataraw, cookies=c, verify=verify_flag)
			else:
				break

			if response.status_code == 204 and method in {"PATCH","DELETE"}:
				# no content (204) - OK for patch,delete
				t = "deleted" if method == "DELETE" else "updated"
				error = Error({"Code": 2, "Message": str(response.status_code) + ": object was " + t})
				retry  = False
			elif response.status_code == 201 and method == "POST":
				# Created (201) - OK for post
				error = Error({"Code": 2, "Message": str(response.status_code) + ": object was created"})
				retry  = False
			elif response.status_code == 404:
				error = Error({"Code": 1, "Message": str(response.status_code) + ": nothing to do"})
				retry  = False
			elif "@odata.context" in response.text:
				retry = False
			elif "Access is denied" in response.text:
				error = Error({"Code": 1, "Message": "Access is denied"})
				retry = False
			elif "File or directory not found" in response.text:
				error = Error({"Code": 1, "Message": "File or directory not found"})
				retry = False
			else:
				# unknown problem, just try authenticate one time
				auth()
		except:
			# if file with cookies not found or cookie file is incorrect
			auth()
		if not retry:
			break
	
	# check error/status 1
	if error is not None:
		if error.Code != 0:
			status = False
			return error.toJSON()
	
	# error. but not in json format
	try:
		js = json.loads(response.text)
	except:
		msg = "" if response is None else response.text
		error = Error({"Code": 1, "Message": msg})
		return error.toJSON()

	# check error 2
	if "@odata.context" not in response.text:
		if js.get("error") != None:
			payload = {"Code": 1, "Message": json.dumps(js["error"])}
		else:
			payload = {"Code": 1, "Message": response.text}
		error = Error(payload)
		return error.toJSON()

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
					dc = datetime.strptime(j["CreatedOn"][0:19], "%Y-%m-%dT%H:%M:%S")
					dm = datetime.strptime(j["ModifiedOn"][0:19], "%Y-%m-%dT%H:%M:%S")
					s = s + "\"CreatedOn\":\"" + dc.strftime("%Y-%m-%d %H:%M:%S") +"\","
					s = s + "\"ModifiedOn\":\"" + dm.strftime("%Y-%m-%d %H:%M:%S") +"\","

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
def main():
	if method == "GET":
		coll_list = collection.split(",")
		for c in coll_list:
			s = call("GET",c)
			if outto == "console":
				out.write(s)
			else:
				with open(f"{filepath}/{c}.json", 'wt', encoding='utf-8') as f:
					f.write(s)
	elif method == "POST":
		coll_list = collection.split(",")
		s = call(method,coll_list[0])
		if outto == "console":
			out.write(s)
		else:
			with open(f"{filepath}/{c}_post.json", 'wt', encoding='utf-8') as f:
				f.write(s)
	elif method in ("PATCH","DELETE"):
		# b.e. Contact(c31c7862-fe33-4a13-9bbc-0943fa08fd02)
		coll_list = collection.split(",")
		s = call(method,coll_list[0])
		if outto == "console":
			out.write(s)
		else:
			with open(f"{filepath}/{c}_patch.json", 'wt', encoding='utf-8') as f:
				f.write(s)
	elif method == "METADATA" and collection != "ALL":
		s = call("GET","")
		if outto == "console":
			out.write(s)
		else:
			with open(f"{filepath}/metadata.json", 'wt', encoding='utf-8') as f:
				f.write(s)
	# loop. for test only
	elif method == "METADATA" and collection == "ALL":
		s = call("GET","")
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

#****************************************************************************************
main()

