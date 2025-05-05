from PIL import Image  # Ajout de l'importation manquante
import streamlit as st
import pandas as pd
import pdfkit
import math
import tempfile
import os
import json  # Ajout de l'importation pour JSON

# -----------------------
# Chargement des configurations JSON
# -----------------------

st.markdown("### 📂 Charger une configuration JSON")
uploaded_file = st.file_uploader("Importer un fichier JSON", type=["json"])


if uploaded_file is not None:
    try:
        # Charger les données depuis le fichier JSON
        config_data = json.load(uploaded_file)

        # Vérifier que les clés du fichier JSON correspondent à celles de st.session_state
        for key, value in config_data.items():
            if key in st.session_state:
                st.session_state[key] = value
            elif key == "facteur":  # Gestion spécifique pour la clé "facteur"
                if value in facteur():  # Vérifier si la valeur est valide
                    option = value  # Mettre à jour l'option sélectionnée
                    st.session_state["facteur"] = facteur[value]  # Mettre à jour le facteur
                else:
                    st.warning(f"⚠️ Valeur invalide pour 'facteur' : {value}")
            else:
                st.warning(f"⚠️ Clé inconnue dans le fichier JSON : {key}")

        st.success("✅ Configuration chargée avec succès !")
    except json.JSONDecodeError:
        st.error("❌ Le fichier JSON est mal formaté. Veuillez vérifier sa structure.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'importation : {e}")



st.markdown("---")

# -----------------------
# Sauvegarde des données
# -----------------------

def sauvegarder_donnees(data, filename="config_ecs.json"):
    """Sauvegarde les données dans un fichier JSON."""
    with open(filename, "w") as f:
        json.dump(data, f)

def charger_donnees(filename="config_ecs.json"):
    """Charge les données depuis un fichier JSON."""
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return None


# -----------------------
# Donnéss de base
# -----


# Définir le chaleur spécifique de l'eau (J/kg·K)
cp = 4.187

# Définir le nombre moyen d'occupants par typologie d'appartement
typologie_occupants = {
    "2 pièces": 1.5,
    "3 pièces": 2,
    "4 pièces": 3,
    "5 pièces": 4,
    "6 pièces": 5
}


# -----------------------
# Initialisation de st.session_state
# -----------------------

def initialiser_session_state():
    if "appartements" not in st.session_state:
        st.session_state["appartements"] = {
            "2 pièces": 0,
            "3 pièces": 0,
            "4 pièces": 0,
            "5 pièces": 0,
            "6 pièces": 0,
        }
    if "litres_par_personne_Vwui" not in st.session_state:
        st.session_state["litres_par_personne_Vwui"] = 50
    if "t_min" not in st.session_state:
        st.session_state["t_min"] = 10
    if "t_max" not in st.session_state:
        st.session_state["t_max"] = 60
    if "cycles" not in st.session_state:
        st.session_state["cycles"] = 2
    if "temps_chauffe" not in st.session_state:
        st.session_state["temps_chauffe"] = 3
    if "boiler_type" not in st.session_state:
        st.session_state["boiler_type"] = "Type a"
    if "volume_reel_boiler" not in st.session_state:
        st.session_state["volume_reel_boiler"] = 1000
    if "nr_chauffeau" not in st.session_state:
        st.session_state["nr_chauffeau"] = 1
    if "commentaire" not in st.session_state:
        st.session_state["commentaire"] = ""

initialiser_session_state()

# -----------------------
# Interface utilisateur
# -----------------------



st.header("🏭 Dimensionnement groupe ECS")
st.markdown("🏢 Typologie des appartements")
st.markdown("Veuillez entrer le nombre d'appartements pour chaque typologie.")

# Utilisation de colonnes pour réduire l'espace vertical
col1, col2, col3 = st.columns(3)

with col1:
    st.session_state["appartements"]["2 pièces"] = st.number_input(
        "2 pièces", min_value=0, value=st.session_state["appartements"]["2 pièces"], step=1
    )
    st.session_state["appartements"]["5 pièces"] = st.number_input(
        "5 pièces", min_value=0, value=st.session_state["appartements"]["5 pièces"], step=1
    )
with col2:
    st.session_state["appartements"]["3 pièces"] = st.number_input(
        "3 pièces", min_value=0, value=st.session_state["appartements"]["3 pièces"], step=1
    )
    st.session_state["appartements"]["6 pièces"] = st.number_input(
        "6 pièces", min_value=0, value=st.session_state["appartements"]["6 pièces"], step=1
    )
with col3:
    st.session_state["appartements"]["4 pièces"] = st.number_input(
        "4 pièces", min_value=0, value=st.session_state["appartements"]["4 pièces"], step=1
    )

# Exemple de calcul dynamique
total_personnes = sum(
    st.session_state["appartements"][typologie]
    for typologie in st.session_state["appartements"]
)
st.markdown(f"👥 Nombre total de personnes : `{total_personnes}`")



st.markdown(f"💧(Vw,u,i) 𝑉𝑜𝑙𝑢𝑚𝑒 d'eau utile par personne [l]")
litres_par_personne_Vwui = st.number_input("Litres d'eau chaude par personne", min_value=10, max_value=150, value=50)



col1, col2 = st.columns(2)
with col1:
    t_min = st.number_input("Température de l'eau froide (°C)", min_value=0, max_value=50, value=10)
with col2:
    t_max = st.number_input("Température de l'eau chaude souhaitée (°C)", min_value=50, max_value=65, value=60)





# Calcul dynamique du volume utile AVANT l'affichage des besoins en chaleur
volume_utile = total_personnes * litres_par_personne_Vwui
st.markdown(
    f"💧 (Vw,i) **Volume utile d'eau chaude requis :** {volume_utile:.2f} l")



besoin_chaleur = total_personnes * litres_par_personne_Vwui * (t_max-t_min) * 0.00116
st.markdown(f"💧 (Qw)**Besoins en chaleur pour l'eau chaude** : {besoin_chaleur:.2f} kWh ")
st.markdown("---")



# Calcul dynamique du volume d'eau chaude produite
volume_produite = volume_utile * 1.5
st.markdown(f"💧 (Vw,d,1)**Volume d'eau chaude produite (150%)** : {volume_produite:.2f} l ")



col3, col4 = st.columns(2)
with col3:
    cycles = st.number_input("🔄 Nombre de cycles par jour", min_value=1, value=2)
with col4:
    temps_chauffe = st.number_input("🕐 Temps de chauffe par cycle (en heures)", min_value=1, value=3)


# Calcul dynamique du volume d'eau chaude produite
volume_commande = volume_produite / cycles
st.markdown(f"💧 (Vw,sto,ctr,1)**Volume de commande* : {volume_commande:.2f} l ")
# Introduction de formule polinomiale pour le calcul du taux de consommation de pointe  en 1 heure
t_pointe = (-2.98e-6 * total_personnes *3 + 0.00223 * total_personnes *2 - 0.51514 * total_personnes + 49.67)/100
# Calcul dynamique du volume de couverture
volume_couverture = t_pointe * volume_produite
st.markdown(f"💧 (Vw,sto,pk)**Volume de couverture* : {volume_couverture:.2f} l ")



option = st.radio(
    "Sélectionne le type de boiler",
    ("Type a", "Type b", "Type c"),
    horizontal=True,
    index=["Type a", "Type b", "Type c"].index(st.session_state["boiler_type"]),  # Restaure la sélection
    key="boiler_selector"
)

image_paths = {
    "Type a": "a_boiler.png",
    "Type b": "b_boiler.png",
    "Type c": "c_boiler.png"
}

facteur = {
    "Type a": 1.25,
    "Type b": 1.1,
    "Type c": 1
}



st.image(image_paths[option], caption=f"Configuration sélectionnée : {option}", width=240)

facteur = facteur[option]
# Calcul dynamique du volume initiale du chauffeau
volume_initiale = (volume_commande + volume_couverture) * facteur
st.markdown(f"💧 (Vw,sto,1)**Volume de initiale du chauffeau* : {volume_initiale:.2f} l ")
st.markdown("---")



# Ajout du champ pour le volume réel ou commercialisé
volume_reel_boiler = st.number_input(
    "Volume normalisé du chauffeau (l)",
    min_value=300, value=1000, step=1, format="%d"
)
# Ajout quantité de chauffchauffe-eaux
nr_chauffeau = st.number_input(
    "Quantité de chauffe-eaux",
    min_value=1, value=1, step=1, format="%d"
)

# Calcul dynamique du volume réel

volume_reel_groupe = volume_reel_boiler*nr_chauffeau
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown(f"💧 (Vw,sto,2)**Volume groupe ECS** : {volume_reel_groupe:.2f} l")
if "volume_reel_groupe" not in st.session_state:
    st.session_state["volume_reel_groupe"] = 0  # Valeur par défaut

with col2:
    commentaire = st.text_area("Ajouter un commentaire :", placeholder="Entrez marque et modèle du chauffe-eau", height=100)



st.markdown("---")



# Calcul des pertes thermiques du accumulateur. Pertes par volume réel(kWh/jour)
volumes = [5, 30, 50, 80, 100, 120, 150, 200, 300, 400, 500, 600, 800, 1000, 1250, 1500, 2000]
pertes_limites = [0.35, 0.60, 0.78, 0.98, 1.10, 1.20, 1.35, 1.56, 1.91, 2.20, 2.46, 2.69, 3.11, 3.48, 3.89, 4.26, 4.92]
# Interpolation linéaire pour les pertes thermiques
def interpolation_lineaire(x, x_points, y_points):
    if x <= x_points[0]:
        return y_points[0]
    if x >= x_points[-1]:
        return y_points[-1]
    for i in range(1, len(x_points)):
        if x < x_points[i]:
            # Interpolation linéaire
            x0, x1 = x_points[i-1], x_points[i]
            y0, y1 = y_points[i-1], y_points[i]
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return y_points[-1]
# Calcul des pertes thermiques du accumulateur
perte_limite = interpolation_lineaire(volume_reel_groupe, volumes, pertes_limites)
 # Ajout du champ pour le nombre de raccordements hydrauliques
c2 = st.number_input(
    "Nombre de raccordements hydrauliques par accumulateur ECS",
    min_value=2, value=2, step=1, format="%d"
)
# Calcul des pertes thermiques du accumulateur
if c2 > 2:
    pertes_raccordement = (c2 - 2) * 0.11
else:
    pertes_raccordement = 0.0

if volume_reel_boiler <= 2000:
    Qw_sto_is = perte_limite + pertes_raccordement
    st.markdown(
        f"🔹 **$(Q_{{w,sto,is}})$ Pertes de stockage** : `{Qw_sto_is:.2f} kWh/jour`"
    )
else:
    Qw_sto_is = 0.11 * math.sqrt(volume_reel_boiler) + 0.1 * (c2 - 2)
    st.markdown(
        f"🔹 **$(Q_{{w,sto,is}})$ Pertes de stockage** : `{Qw_sto_is:.2f} kWh/jour`"
    )
    

# Affichage du module de sélection des tubes à droite
col_gauche, col_droite = st.columns([2, 1])

with col_gauche:
    st.markdown("🔹 **$(Q_{{w,hi,is}})$ Pertes thermiques journalières d'une maintenue en température Δθ=35K**")
    diametres = [15, 18, 22, 28, 35, 42, 54, 64, 76, 88, 108]
    pertes_par_metre = [0.083, 0.088, 0.094, 0.102, 0.110, 0.117, 0.127, 0.134, 0.143, 0.150, 0.160]
    diametre_pertes = dict(zip(diametres, pertes_par_metre))

    col_tube1, col_tube2, col_tube3, col_total = st.columns(4)

with col_tube1:
    st.markdown("**Tube n°1 (⌀-m)**")
    diam1 = st.selectbox("Diamètre (mm)", diametres, key="diametre_1", label_visibility="collapsed")
    long1 = st.number_input("Longueur (m)", min_value=0, value=0, step=1, key="longueur_1", label_visibility="collapsed")
    perte1 = diametre_pertes[diam1] * long1
    st.markdown(f"<span style='color:green'>{perte1:.3f} kWh/jour</span>", unsafe_allow_html=True)

with col_tube2:
    st.markdown("**Tube n°2 (⌀-m)**")
    diam2 = st.selectbox("Diamètre (mm)", diametres, key="diametre_2", label_visibility="collapsed")
    long2 = st.number_input("Longueur (m)", min_value=0, value=0, step=1, key="longueur_2", label_visibility="collapsed")
    perte2 = diametre_pertes[diam2] * long2
    st.markdown(f"<span style='color:green'>{perte2:.3f} kWh/jour</span>", unsafe_allow_html=True)

with col_tube3:
    st.markdown("**Tube n°3 (⌀-m)**")
    diam3 = st.selectbox("Diamètre (mm)", diametres, key="diametre_3", label_visibility="collapsed")
    long3 = st.number_input("Longueur (m)", min_value=0, value=0, step=1, key="longueur_3", label_visibility="collapsed")
    perte3 = diametre_pertes[diam3] * long3
    st.markdown(f"<span style='color:green'>{perte3:.3f} kWh/jour</span>", unsafe_allow_html=True)

with col_total:
    Qw_hi_is = perte1 + perte2 + perte3
    st.markdown(f"<span style='color:green'><b>Q = {Qw_hi_is:.3f} kWh/jour</b></span>", unsafe_allow_html=True)


st.markdown("---")



# Calcul dynamique des besoins en chaleur réel pour chaque cycle
Qw = volume_reel_groupe * 0.00116 * (t_max - t_min)
Qw_gen_out = Qw + Qw_sto_is + Qw_hi_is
st.markdown(
    f"🔺 **$(Q_{{w,gen,out}})$Besoins de chaleur à fournir à chaque cycle de recharge :** `{Qw_gen_out:.2f} kW`"
)   


# Calcul dynamique pour la puissance du groupe
Qw_gen = Qw_gen_out/temps_chauffe
st.markdown(
    f"🔺 **$(Q_{{w,gen}})$Puissance du groupe ECS :** `{Qw_gen:.2f} kWh`"
)


st.markdown("---")

# -----------------------
# Calcul des résultats (automatique)
# -----------------------

# Calcul des résultats principaux
total_personnes = sum(
    st.session_state["appartements"][typologie] * typologie_occupants[typologie]
    for typologie in typologie_occupants
)

volume_utile = total_personnes * st.session_state["litres_par_personne_Vwui"]
delta_t = st.session_state["t_max"] - st.session_state["t_min"]  # Calcul de l'écart de température
puissance_kw = (volume_utile * cp * delta_t) / (st.session_state["temps_chauffe"] * 3600 * st.session_state["cycles"])

# Affichage des résultats
st.markdown("### ✅ Résultats")
st.success(f"👥 **Nombre total de personnes :** `{total_personnes:.1f}`")
st.info(f"💧 **Volume total du groupe ECS :** `{volume_reel_groupe:.1f} l. Quantité de boilers {nr_chauffeau:.0f}. {commentaire}`")
st.info(f"🔄 **Cycles :** `{cycles:.0f} Cycles par jour pour {temps_chauffe:.1f} heures par cycle`")
st.warning(f"🔥 **Puissance thermique nécessaire :** `{Qw_gen_out:.2f} kW`")



# -----------------------
# Boutons d'action d'exportation
# -----------------------


st.markdown("### 📤 Enregistrement et export des résultats")
col_button1, col_button2 = st.columns(2)

with col_button1:
    export_pdf = st.button("📄 Exporter les résultats")



# Stockage des résultats pour l'export PDF
st.session_state["resultat_html"] = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Résultats</title>
</head>
<body>
    <h2>Résultats (Groupe ECS)</h2>
    <ul>
        <li><strong>Nombre de personnes :</strong> {total_personnes:.1f}</li>
        <li><strong>Volume d'eau chaude :</strong> {volume_reel_boiler:.1f} L</li>
        <li><strong>Puissance thermique :</strong> {Qw_gen:.2f} kW</li>
        <li><strong>ΔT :</strong> {delta_t} °C</li>
    </ul>
</body>
</html>
"""

# -----------------------
# exporter des résultats en PDF
# -----------------------

if export_pdf:
    if "resultat_html" in st.session_state:
        try:
            # Configuration de pdfkit avec le chemin vers wkhtmltopdf
            config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
            
            # Création d'un fichier temporaire pour le PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                pdfkit.from_string(st.session_state["resultat_html"], f.name, configuration=config)
                temp_pdf_path = f.name  # Stocker le chemin temporaire

            # Bouton pour télécharger le PDF
            with open(temp_pdf_path, "rb") as file:
                st.download_button("⬇️ Télécharger le PDF", data=file, file_name="dimensionnement_boiler.pdf", mime="application/pdf")
            
            # Suppression du fichier temporaire après téléchargement
            os.unlink(temp_pdf_path)
            st.success("📄 Résultat exporté avec succès.")
        except Exception as e:
            st.error(f"Une erreur est survenue lors de l'exportation du PDF : {e}")
    else:
        st.warning("Veuillez d'abord effectuer un calcul pour exporter les résultats.")


# -----------------------
# exporter des résultats en JSON
# -----------------------








with col_button2:
    if st.button("📁 Exporter les données JSON"):
    # Préparer les données à exporter
        donnees = {
        "appartements": {typologie: int(st.session_state["appartements"][typologie]) for typologie in st.session_state["appartements"]},
        "litres_par_personne_Vwui": float(st.session_state["litres_par_personne_Vwui"]),
        "t_min": float(st.session_state["t_min"]),
        "t_max": float(st.session_state["t_max"]),
        "cycles": int(st.session_state["cycles"]),
        "temps_chauffe": int(st.session_state["temps_chauffe"]),
        "facteur": facteur[option],
        "volume_reel_groupe": int(st.session_state["volume_reel_groupe"]),
        "nr_chauffeau": int(st.session_state["nr_chauffeau"]),
        "nr_chauffeau": int(st.session_state["nr_chauffeau"]),
        "commentaire": st.session_state["commentaire"]
    }


    # Convertir les données en JSON
        json_data = json.dumps(donnees, indent=4)

    # Bouton pour télécharger le fichier JSON
        st.download_button(
        label="⬇️ Télécharger les données",
        data=json_data,
        file_name="donnees_dimensionnement.json",
        mime="application/json"
    )
