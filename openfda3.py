import socket

IP = "127.0.0.1"
PORT = 9006
MAX_OPEN_REQUESTS = 5

import http.client
import json

def process_client(clientsocket):

    # Read the request message. It comes from the socket
    # What are received are bytes. We will decode them into an UTF-8 string
    request_msg = clientsocket.recv(1024).decode("utf-8")
    request_msg = request_msg.replace("\r", "").split("\n")
    request_line = request_msg[0]
    request = request_line.split(" ")
    req_cmd = request[0]
    path = request[1]

    print("")
    print("REQUEST: ")
    print("Command: {}".format(req_cmd))
    print("Path: {}".format(path))
    print("")

    headers = {'User-Agent': 'http-client'}

    conn = http.client.HTTPSConnection("api.fda.gov")
    conn.request("GET", "/drug/label.json?limit=10", None, headers)
    r1 = conn.getresponse()
    print(r1.status, r1.reason)
    repos_raw = r1.read().decode("utf-8")
    conn.close()

    repos = json.loads(repos_raw)

    # let's try to write them down in an html file
    f = open('labels.html', 'w')
    f.write('<html><head><h1>DRUG LABEL LIST</h1><body style="background-color: green">')
    for i in range(len(repos['results'])):
        try:
            drug = repos['results'][i]["openfda"]["generic_name"][0]
            f.write('\n<li>')
            f.write(' generic name is: ')
            f.write(drug)
            f.write('</li>')  # this will be removed when \n error is fixed
        except KeyError:
            continue
    f.close()

    # Read the html page to send, depending on the path
    if path == "/":
        filename = "labels.html"
    else:
        filename = "error.html"

    print("File to send: {}".format(filename))

    with open(filename, "r") as g:
        content = g.read()

    # -- Everything is OK
    status_line = "HTTP/1.1 200 OK\n"

    # -- Build the header
    header = "Content-Type: text/html\n"
    header += "Content-Length: {}\n".format(len(str.encode(content)))

    # -- Busild the message by joining together all the parts
    response_msg = str.encode(status_line + header + "\n" + content)
    clientsocket.send(response_msg)


# Create the server cocket, for receiving the connections
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:

    serversocket.bind((IP, PORT))
    serversocket.listen(MAX_OPEN_REQUESTS)

    while True:

        print("Waiting for clients at IP: {}, Puerto: {}".format(IP, PORT))
        (clientsocket, address) = serversocket.accept()

        # Process the client request
        print("  Client request recgeived. IP: {}".format(address))
        print("Server socket: {}".format(serversocket))
        print("Client socket: {}".format(clientsocket))
        process_client(clientsocket)
        clientsocket.close()

except socket.error:
    print("Socket error. Problemas with the PORT {}".format(PORT))
    print("Launch it again in another port (and check the IP)")
