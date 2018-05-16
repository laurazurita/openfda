
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
        elif 'listCompanies' in path:
            limit = None
            if len(path.split("?")) > 1:
                limit = path.split("?")[1].split("=")[1]
            itms = client.listDrug(limit)
            resp = html.listhtml(parser.parsecomps(itms))

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

        elif 'searchDrug' in path:
            act_ing = None
            limit = 10
            parameters = path.split("?")[1].split("&")
            for parameter in parameters:
                name = parameter.split("=")[0]
                value = parameter.split("=")[1]
                if name == 'active_ingredient':
                    act_ing = value
                elif name == 'limit':
                    limit = value
            itms = client.searchDrug(act_ing, limit)
            resp = html.listhtml(parser.parse_drugs(itms))
        elif 'listDrugs' in path:
            limit = None
            if len(path.split("?")) > 1:
                limit = path.split("?")[1].split("=")[1]
            itms = client.listDrug(limit)
            resp = html.listhtml(parser.parse_drugs(itms))
        elif 'listWarnings' in path:
            limit = None
            if len(path.split("?")) > 1:
                limit = path.split("?")[1].split("=")[1]
            itms = client.listDrug(limit)
            resp = html.listhtml(parser.parse_warnings(itms))
        else:
            code = 404
            if not OPENFDA_BASIC:
                url_found = False
                resp = html.notfound()

        self.send_response(code)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(bytes(resp, "utf8"))
        return

class OpenFDAHTML():
    # We create here a list in the html page with the info, using a loop
    def listhtml(self, things):
        list = "<ul>"
        for thing in things:
            list += "<li>" + thing + "</li>"
        list += "</ul>"
        return list

    # If not found, it should give back an error, and for that, we use a specific html file the not_found.html
    def notfound(self):
        with open("not_found.html") as file:
            file = file.read()
        return file
class OpenFDAClient():

    def sendquery(self, query):

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
        query = "search=active_ingredient:%s&limit=%s" % (active_ingredient, limit)
        info = self.send_query(query)
        return info

    def listDrug(self, limit=10):
        query = "limit=" + str(limit)
        drugs = self.sendquery(query)
        return drugs

    def searchCompany(self, compname, limit=10):
        # We request the company name so the client looks up for it
        query = 'search=openfda.manufacturer_name:"%s"' % compname
        if limit:
            query += "&limit=" + str(limit)
        drugs = self.sendquery(query)
        return drugs


class OpenFDAParser():

    def parsecomps(self, drugs):

        # We create an empty list of the companies
        companies = []
        for drug in drugs:
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                companies.append(drug['openfda']['manufacturer_name'][0])
            else:
                companies.append("Unknown")
            companies.append(drug['id'])
        return companies

    def parse_drugs(self, drugs):
        # We create an empty list of the labels of the drugs:
        drugs_labels = []

        for drug in drugs:
            label = drug['id']
            if 'active_ingredient' in drug:
                label += " " + drug['active_ingredient'][0]
            if 'openfda' in drug and 'manufacturer_name' in drug['openfda']:
                label += " " + drug['openfda']['manufacturer_name'][0]
            drugs_labels.append(label)
        return drugs_labels

    def parse_warnings(self, drugs):
        # We extract a warnings list:
        warnings = []
        for drug in drugs:
            if 'warnings' in drug and drug['warnings']:
                warnings.append(drug['warnings'][0])
            else:
                warnings.append("None")
        return warnings


Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()