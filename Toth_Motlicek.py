import requests
import json

from flask import Flask, request, jsonify, send_from_directory, render_template

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True

class Kraj:
    pocet_muzov = 0
    pocet_zien = 0
    celkovy_vek_muzi = 0
    celkovy_vek_zeny = 0

    def __init__(self, name, code, type):
        self.name = name
        self.code = code
        self.type = type

    def pridat_infikovanych(self, pohlavie, vek):
        if pohlavie == "M":
            self.pocet_muzov += 1
            self.celkovy_vek_muzi += vek
        elif pohlavie == "Z":
            self.pocet_zien += 1
            self.celkovy_vek_zeny += vek
            
    def get_json(self):
        pocet_nakazenych = self.pocet_muzov + self.pocet_zien
        priemer_vek = (self.celkovy_vek_zeny + self.celkovy_vek_muzi)/pocet_nakazenych
        priemer_vek_zeny = self.celkovy_vek_zeny / self.pocet_zien
        priemer_vek_muzi = self.celkovy_vek_muzi / self.pocet_muzov
        podiel_muzov = self.pocet_muzov / pocet_nakazenych * 100
        vysledek = {"total_infected": pocet_nakazenych, "avg_age": round(priemer_vek,2),
                    "avg_age_women": round(priemer_vek_zeny, 2), "avg_age_men": round(priemer_vek_muzi,2),
                    "men": round(podiel_muzov, 2), "women": round(100-podiel_muzov, 2),
                    "code": self.code, "name": self.name}
        return vysledek
        
        

r = requests.get("http://arccr-arcdata.opendata.arcgis.com/datasets/38f135cb51b347e09f2a65cdc8a06247_19.geojson")
r = r.json()

#nacitanie krajov
kraje = []
for i in range (14):
    kraje.append(Kraj(r["features"][i]["properties"]['NAZ_CZNUTS3'],r["features"][i]["properties"]['KOD_CZNUTS3'],
                      r["features"][i]["geometry"]["type"]))

# Nacitanie chorych
chori = requests.get("https://onemocneni-aktualne.mzcr.cz/api/v1/covid-19/osoby.json")
chori = chori.json()
   
for osoba in chori["data"]:
    k = 0
    while kraje[k].code != osoba["KHS"]:
        k += 1
    i = k    

kraje[i].pridat_infikovanych(osoba["Pohlavi"], int(osoba["Vek"]))


#------------------FLASK--------------
@app.route("/covid_kraje", methods=["GET"])
def covid_kraje():
    kraj = request.args.get("kraj", "0")

    for kod in range(len(kraje)):
        if kraje[kod].code == kraj:
            index = kod
            not_found= False
            break
        else:
            not_found = True

    if not_found:
        return "Chyba"
    else:
        result = kraje[index].get_json()
        result = jsonify(result)
        return result
@app.route("/covid_kraje_json", methods = ["GET"])
def covid_kraje_json():
    features = []

    for i in range(len(kraje)):
        features.append({"type" : "Feature", "properties": kraje[i].get_json()})

    results = {"type": "FeaturesCollection","features": features}
    return jsonify(results)
    
@app.route("/", methods = ["GET"])
def index():
    return render_template("index.html")
    #return f"Pre jednotlive kraje: /kraj?CISLOKRAJA(CZxxx) --------------------<a href='http://127.0.0.1:5000/covid_kraje_json'>Pre vsetky kraje tu</a>"
    
@app.route('/leaflet', methods = ['GET'])
def leaflet():
   return send_from_directory('.', 'leaflet.html')


if __name__ == '__main__':
    app.run(debug=True)