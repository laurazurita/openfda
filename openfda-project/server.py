

import http.server
import json
import socketserver

socketserver.TCPServer.allow_reuse_address = True

PORT = 8000

OPENFDA_BASIC = False

# We are going to use classes. The class is a fundamental building block used in Python, works as a library of objects.

class OpenFDAClient():

    def send_query(self, query):
        # We request an information ("query") to the openfda API, it will return the result of the query in JSON format.
        headers = {'User-Agent': 'http-client'}
        conn = http.client.HTTPSConnection("api.fda.gov")
        # Get a  drug label from the URL and extract the id, the purpose of the drug and the manufacturer_name.
        query_url = "/drug/label.json"
        if query:
            query_url += "?" + query
        print("Sending to OpenFDA the query", query_url)

        conn.request("GET", query_url, None, headers)
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

    def search_drugs(self, active_ingredient, limit=10):
        # We request the drugs so the client looks up for it
        query = 'search=active_ingredient:"%s"' % active_ingredient
        if limit:
            query += "&limit=" + str(limit)
        drugs = self.send_query(query)
        return drugs

    def list_drugs(self, limit=10):
        query = "limit=" + str(limit)
        drugs = self.send_query(query)
        return drugs

    def search_companies(self, company_name, limit=10):
        # We request the company name so the client looks up for it
        query = 'search=openfda.manufacturer_name:"%s"' % company_name
        if limit:
            query += "&limit=" + str(limit)
        drugs = self.send_query(query)
        return drugs


class html_openfda():

    def build_html_list(self, items):
        html_list = "<ul>"
        for item in items:
            html_list += "<li>" + item + "</li>"
        html_list += "</ul>"
        return html_list

    # If not found, it should give back an error, and for that, we use a specific html file the not_found.html
    def get_not_found_page(self):
        with open("not_found.html") as html_file:
            html = html_file.read()
        return html

class parser_openfda():

    def parse_companies(self, drugs):

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

class testHTTPRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        client = OpenFDAClient()
        html_vis = html_openfda()
        parser = parser_openfda()

        http_response_code = 200
        http_response = "<h1>Not supported</h1>"

        if self.path == "/":
            # Return the HTML form for searching
            with open("openfda.html") as file_form:
                form = file_form.read()
                http_response = form
        elif 'searchDrug' in self.path:
            active_ingredient = None
            limit = 10
            params = self.path.split("?")[1].split("&")
            for param in params:
                param_name = param.split("=")[0]
                param_value = param.split("=")[1]
                if param_name == 'active_ingredient':
                    active_ingredient = param_value
                elif param_name == 'limit':
                    limit = param_value
            items = client.search_drugs(active_ingredient, limit)
            http_response = html_vis.build_html_list(parser.parse_drugs(items))
        elif 'listDrugs' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = client.list_drugs(limit)
            http_response = html_vis.build_html_list(parser.parse_drugs(items))
        elif 'searchCompany' in self.path:
            company_name = None
            limit = 10
            params = self.path.split("?")[1].split("&")
            for param in params:
                param_name = param.split("=")[0]
                param_value = param.split("=")[1]
                if param_name == 'company':
                    company_name = param_value
                elif param_name == 'limit':
                    limit = param_value
            items = client.search_companies(company_name, limit)
            http_response = html_vis.build_html_list(parser.parse_companies(items))
        elif 'listCompanies' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = client.list_drugs(limit)
            http_response = html_vis.build_html_list(parser.parse_companies(items))
        elif 'listWarnings' in self.path:
            limit = None
            if len(self.path.split("?")) > 1:
                limit = self.path.split("?")[1].split("=")[1]
            items = client.list_drugs(limit)
            http_response = html_vis.build_html_list(parser.parse_warnings(items))
        else:
            http_response_code = 404
            if not OPENFDA_BASIC:
                url_found = False
                http_response = html_vis.get_not_found_page()

        self.send_response(http_response_code)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        self.wfile.write(bytes(http_response, "utf8"))
        return

Handler = testHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()