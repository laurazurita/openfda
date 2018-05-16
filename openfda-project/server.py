import http.server
import json
import socketserver

socketserver.TCPServer.allow_reuse_address = True

IP = "localhost"
PORT = 8000

OPENFDA_BASIC = False

# We are going to use classes.
class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):

        path = self.path
        html = OpenFDAHTML()
        client = OpenFDAClient()
        parser = OpenFDAParser()

        code = 200
        resp = "<h1>Not supported</h1>"

        if path == "/":
            # Return the HTML form for searching
            with open("html_openfda.html") as file:
                frm = file.read()
                resp = frm

        elif 'searchCompany' in path:
            compname = None
            limit = 10
            parameters = path.split("?")[1].split("&")
            for parameter in parameters:
                name = parameter.split("=")[0]
                value = parameter.split("=")[1]
                if name == 'company':
                    compname = value
                elif name == 'limit':
                    limit = value
            itms = client.searchCompany(compname, limit)
            resp = html.listhtml(parser.parsecomps(itms))
        elif 'listCompanies' in path:
            limit = None
            if len(path.split("?")) > 1:
                limit = path.split("?")[1].split("=")[1]
            items = client.listDrug(limit)
            resp = html.listhtml(parser.parsecomps(items))
        elif 'searchDrug' in path:
            act_ing = None
            limit = 10
            params = path.split("?")[1].split("&")
            for param in params:
                name = param.split("=")[0]
                value = param.split("=")[1]
                if name == 'active_ingredient':
                    act_ing = value
                elif name == 'limit':
                    limit = value
            things = client.searchDrug(act_ing, limit)
            resp = html.listhtml(parser.parse_drugs(things))
        elif 'listDrugs' in path:
            limit = None
            if len(path.split("?")) > 1:
                limit = path.split("?")[1].split("=")[1]
            things = client.listDrug(limit)
            resp = html.listhtml(parser.parse_drugs(things))
        elif 'listWarnings' in path:
            limit = None
            if len(path.split("?")) > 1:
                limit = path.split("?")[1].split("=")[1]
            things = client.listDrug(limit)
            resp = html.listhtml(parser.parse_warnings(things))
        else:
            code = 404
            if not OPENFDA_BASIC:
                url_found = False
                resp = html.get_not_found_page()

        self.send_response(code)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(bytes(resp, "utf8"))
        return

class OpenFDAHTML():

    def listhtml(self, things):
        list = "<ul>"
        for thing in things:
            list += "<li>" + thing + "</li>"
        list += "</ul>"
        return list

    # If not found, it should give back an error, and for that, we use a specific html file the not_found.html
    def get_not_found_page(self):
        with open("not_found.html") as file:
            file = file.read()
        return file
class OpenFDAClient():

    def send_query(self, query):
        # We request an information ("query") to the openfda API, it will return the result of the query in JSON format.
        headers = {'User-Agent': 'http-client'}
        conn = http.client.HTTPSConnection("api.fda.gov")
        # Get a  drug label from the URL and extract the id, the purpose of the drug and the manufacturer_name.
        url = "/drug/label.json"
        if query:
            url += "?" + query
        print("Sending the query", url)

        conn.request("GET", url, None, headers)
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        res_raw = r1.read().decode("utf-8")
        conn.close()

        result = json.loads(res_raw)
        if 'results' in result:
            items = result['results']
        else:
            items = []
        return items

    def searchDrug(self, active_ingredient, limit=10):
        # We request the drugs so the client looks up for it
        query = 'search=active_ingredient:"%s"' % active_ingredient
        if limit:
            query += "&limit=" + str(limit)
        drugs = self.send_query(query)
        return drugs

    def listDrug(self, limit=10):
        query = "limit=" + str(limit)
        drugs = self.send_query(query)
        return drugs

    def searchCompany(self, compname, limit=10):
        # We request the company name so the client looks up for it
        query = 'search=openfda.manufacturer_name:"%s"' % compname
        if limit:
            query += "&limit=" + str(limit)
        info = self.send_query(query)
        return info


class OpenFDAParser():

    def parsecomps(self, info):

        # We create an empty list of the companies
        list = []
        for comp in info:
            if 'openfda' in comp and 'manufacturer_name' in comp['openfda']:
                list.append(comp['openfda']['manufacturer_name'][0])
            else:
                list.append("Unknown")
            list.append(comp['id'])
        return list

    def parse_drugs(self, info):
        # We create an empty list of the labels of the drugs:
        list = []

        for drug in info:
            label = drug['id']
            if 'active_ingredient' in drug:
                label += " " + drug['active_ingredient'][0]
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                label += " " + drug['openfda']['manufacturer_name'][0]
            list.append(label)
        return list

    def parse_warnings(self, info):
        # We extract a warnings list:
        list = []
        for warn in info:
            if 'warnings' in warn and warn['warnings']:
                list.append(warn['warnings'][0])
            else:
                list.append("None")
        return list


Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()