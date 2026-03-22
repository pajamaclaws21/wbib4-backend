import random
import socket
import ssl
import time
import urllib.parse
import base64

from flask import Flask, abort
app = Flask(__name__)

def randomRequestID():
    id = "pjweb-"
    chars = list("qwertyuiopasdfghjklzxcvbnm1234567890")
    for n in range(0, 17):
        id += chars[random.randrange(0, len(chars))]
    return id

currentRequests = []

@app.route("/")
def index():
    thisRequestID = randomRequestID()
    currentRequests.append(thisRequestID)
    return thisRequestID

# from https://browser.engineering/http.html
@app.route("/access/<string:url>/<string:id>")
def access(url, id, redirectNum=0):
    if id in currentRequests:
        # if we've followed more than five redirects, give up
        if redirectNum > 5:
            return "Gave up following redirects"
    
        url = urllib.parse.urlsplit(base64.b64decode(url))  # get the parts of the url
        request = f"GET {url.path.decode('utf-8')} HTTP/1.0\r\nHost: {url.hostname.decode('utf-8')}\r\n\r\n"

        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)  # open socket
    
        # decide what port to listen to
        if url.scheme == b'http':
            port = 80
        elif url.scheme == b'https':
            port = 443

        # if the url has a port in it, decide that port instead
        if url.port != None:
            port = url.port
    
        # open the socket
        s.connect((url.hostname, port))
        # if it's https, use ssl
        if url.scheme == b'https':
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=url.hostname)
            # build the request & send it
        s.send(request.encode("utf8"))
        # get our response & close the socket
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        content = response.read()
        s.close()
    
        # understand the response
        status = int(content.split(" ")[1][0])
        if status == 3:
            return URLrequest(content.split("\r\n")[5].split("Location: ")[1], redirectNum + 1)
        
        currentRequests.remove(id)
        return content
    else:
        abort(401)
