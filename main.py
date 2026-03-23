import random
import socket
import ssl
import time
import urllib.parse
import base64

from flask_cors import CORS
from flask import Flask, abort
app = Flask(__name__)
# only allow the backend to be accessed from my website.
# built with https://regex101.com. would encourage you do this too
CORS(app, origins=r"https:\/\/(www.)?pajamaclaws\.net(\/.*)?")

# self-explanatory
def randomRequestID():
    # adding the string in front makes sure this is a string
    id = "pjweb-"
    chars = list("qwertyuiopasdfghjklzxcvbnm1234567890")
    for n in range(0, 17):
        id += chars[random.randrange(0, len(chars))]
    return id

# self-explanatory; keeps track of all of the current request IDs that have been requested
currentRequests = []

# give out an id
@app.route("/")
def index():
    thisRequestID = randomRequestID()
    currentRequests.append(thisRequestID)
    return thisRequestID

# built from https://browser.engineering/http.html
@app.route("/access/<string:url>/<string:id>")
def access(url, id, redirectNum=0):
    # you must have previously requested the root to get a request ID in order to access a site
    if id in currentRequests:
        # if we've followed more than five redirects, give up
        if redirectNum > 5:
            return "Gave up following redirects"
    
        url = urllib.parse.urlsplit(base64.b64decode(url))  # get the parts of the url
        request = f"GET {url.path.decode('utf-8')} HTTP/1.1\r\nHost: {url.hostname.decode('utf-8')}\r\nConnection: close\r\nUser-agent: pjwbib4\r\n\r\n"

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
            return access(content.split("\r\n")[5].split("Location: ")[1], redirectNum + 1)
        
        currentRequests.remove(id)
        return content
    else:
        abort(401)
