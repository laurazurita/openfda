import http.client
import json

headers = {'User-Agent': 'http-client'}


conn = http.client.HTTPSConnection("api.fda.gov")

conn.request("GET", "/drug/label.json", None, headers)
r1 = conn.getresponse()
print(r1.status, r1.reason)
drugs_raw = r1.read().decode("utf-8")
conn.close()

drugs = json.loads(drugs_raw)
drug = drugs['results'][0]
id = drug['id']
purpose = drug['purpose'][0]
manufacturer = drug['openfda']['manufacturer_name'][0]

print(id,purpose,manufacturer)

# Part two of Practice 1

conn.request("GET", "/drug/label.json?limit=10", None, headers) #Limit 10 drugs
r1 = conn.getresponse()
print(r1.status, r1.reason)
drugs_raw = r1.read().decode("utf-8")
conn.close()

drugs = json.loads(drugs_raw)['results']

for drug in drugs: # Due to the limit stablished is going to take 10 drugs
    print(drug['id'])
