import random
import socket
import ssl
import time
import urllib.parse
import flask
from flask_cors import CORS, cross_origin

app = flask.Flask(__name__)
uaProduct = "WBIB4"
uaVersion = "1.0"

# if you are forking: CHANGE THESE!!
allowedOrigins = ["https://pajamaclaws.net", "https://www.pajamaclaws.net"]
userAgent = "pajamaclaws-net"

CORS(app, origins=allowedOrigins)

def formatUrl(url):
    if "://" not in url or "http" not in url:
        raise Error("url passed to formatter needs a scheme (http/s). Typo?")
    scheme = url.split("://")[0]
    if url[len(url) - 1] != "/":
        url += "/"
    url = url.split(f"{scheme}://")[1].split("/")
    return f"{scheme}|{'|'.join(url)}"

def unformUrl(url):
    if "|" not in url:
        raise Error("this url looks unformatted (does not have |). Typo?")
    if "http" not in url:
        raise Error("url passed needs a scheme (http/s). Typo?")
    url = url.split("|")
    url = f"{url[0]}://{'/'.join(url[1:])}"
    if url[len(url) - 1] != "/":
        url += "/"
    return url

@app.route("/")
def index():
    return app.send_static_file(filename="index.html")

@app.route("/howto")
def howto():
    return app.send_static_file(filename="howto.html")

# base from https://browser.engineering/http.html
@app.route("/api/access/<string:url>")
def access(url, , redirectNum=0):
    if not flask.request.headers.get('origin') in allowedOrigins:
        flask.abort(401)

    # if we've followed more than five redirects, give up
    if redirectNum > 5:
        return "Gave up following redirects"
        
    url = urllib.parse.urlsplit(unformUrl(url))  # get the parts of the url
    request = "\r\n".join([f"GET {url.path} HTTP/1.0", f"User-Agent: {uaProduct}/{uaVersion} {userAgent}", "Connection: close", "X-Powered-By: wbib4", f"Host: {url.hostname}", "\r\n"])

    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)  # open socket
    # decide what port to listen to
    if url.scheme == "http":
        port = 80
    elif url.scheme == "https":
        port = 443
    
    # if the url has a port in it, decide that port instead
    if url.port != None:
        port = url.port
    
    # open the socket
    s.connect((url.hostname, port))
    # if it's https, use ssl
    if url.scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=url.hostname)
    # build the request & send it
    s.send(request.encode("utf8"))
    # get our response & close the socket
    response = s.makefile("r", encoding="utf8", newline="\r\n")
    content = response.read()
    s.close()

    # allows us to better understand content
    content = content.split("\r\n")

    httpDict = {}
    finalReturn = []

    for item in content:
        index = content.index(item)
        if ": " in item and index != len(content) - 1:
            # adds response data to a dictionary
            item = item.split(": ")
            key = item[0]
            value = item[1]
            httpDict[key] = value
        elif "HTTP/" in item:
            # adds data about response to output: HTTP version, status code, status name
            finalReturn.append([item[:8], item.split(" ")[1], item[13:]])
        elif item != "":
            # add all non-empty items to final value
            finalReturn.append(item)

    # makes setup of list as follows: HTTP version/code/name, response data, response body
    finalReturn.insert(1, httpDict)
        
    # checks that the status code is not a redirect
    if finalReturn[0][1][0] == "3":
        try:
            location = httpDict["location"]
        except:
            location = httpDict["Location"]

        return access(formatUrl(location), id, redirectNum+1)
    
    return finalReturn