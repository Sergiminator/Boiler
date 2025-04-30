from PIL import Image  # Ajout de l'importation manquante
import streamlit as st
import pdfkit
import tempfile
import os
import json  # Ajout de l'importation pour JSON


# -----------------------
# Paramètres de base
# -----------------------

typologie_occupants = {
    "2 pièces": 1.5,
    "3 pièces": 2,
    "4 pièces": 3,
    "5 pièces": 4,
    "6 pièces": 5
}

cp = 4.187  # kJ/kg°C

# -----------------------
# Interface Streamlit
# -----------------------

col_logo, col_title = st.columns([1, 3])

with col_logo:
    logo = Image.open("logo.png")
    st.image(logo, width=200)

with col_title:
    st.title("📊 Dimensionnement du boiler - méthode SIA 385/2:2015")

st.header("🏢 Typologie des appartements")
appartements = {}
for typologie in typologie_occupants:
    appartements[typologie] = st.number_input(f"Nombre d'appartements {typologie}", min_value=0, value=0, step=1, key=typologie)

# Calcul dynamique et affichage
total_personnes_npi = sum(
    appartements[typologie] * typologie_occupants[typologie]
    for typologie in typologie_occupants
    if appartements[typologie] > 0
)
st.markdown(f"👥 (∑nP,i) **Nombre total de personnes :** `{total_personnes_npi:.1f}`")



st.markdown(f"💧(Vw,u,i) 𝑉𝑜𝑙𝑢𝑚𝑒 d'eau utile par personne [l]")
litres_par_personne_Vwui = st.number_input("Litres d'eau chaude par personne", min_value=10, max_value=150, value=50)



col1, col2 = st.columns(2)
with col1:
    t_min = st.number_input("Température de l'eau froide (°C)", min_value=0, max_value=50, value=10)
with col2:
    t_max = st.number_input("Température de l'eau chaude souhaitée (°C)", min_value=50, max_value=65, value=60)





# Calcul dynamique du volume utile AVANT l'affichage des besoins en chaleur
volume_utile = total_personnes_npi * litres_par_personne_Vwui
st.markdown(
    f"💧 (Vw,i) **Volume utile d'eau chaude requis :** {volume_utile:.2f} l")



besoin_chaleur = total_personnes_npi * litres_par_personne_Vwui * (t_max-t_min) * 0.00116
st.markdown(f"💧 (Qw)**Besoins en chaleur pour l'eau chaude** : {besoin_chaleur:.2f} kWh ")
st.markdown("---")



# Calcul dynamique du volume d'eau chaude produite
volume_produite = volume_utile * 1.5
st.markdown(f"💧 (Vw,d,1)**Volume d'eau chaude produite (150%)** : {volume_produite:.2f} l ")



col3, col4 = st.columns(2)
with col3:
    cycles = st.number_input("Nombre de cycles par jour", min_value=1, value=2)
with col4:
    temps_chauffe = st.number_input("Temps de chauffe par cycle (en heures)", min_value=0.5, value=1)


# Calcul dynamique du volume d'eau chaude produite
volume_commande = volume_produite / cycles
st.markdown(f"💧 (Vw,sto,ctr,1)**Volume de commande* : {volume_commande:.2f} l ")
# Introduction de formule polinomiale pour le calcul du taux de consommation de pointe  en 1 heure
t_pointe = (-2.98e-6 * total_personnes_npi *3 + 0.00223 * total_personnes_npi *2 - 0.51514 * total_personnes_npi + 49.67)/100
# Calcul dynamique du volume de couverture
volume_couverture = t_pointe * volume_produite
st.markdown(f"💧 (Vw,sto,pk)**Volume de couverture* : {volume_couverture:.2f} l ")



option = st.radio(
    "Sélectionne le type de boiler",
    ("Type a", "Type b", "Type c"),
    horizontal=True
    )

image_paths = {
    "Type a": "a_boiler.png",
    "Type b": "b_boiler.png",
    "Type c": "c_boiler.png"
}

facteurs = {
    "Type a": 1.25,
    "Type b": 1.1,
    "Type c": 1
}

st.image(image_paths[option], caption=f"Configuration sélectionnée : {option}", width=240)

facteur = facteurs[option]
# Calcul dynamique du volume initiale du chauffeau
volume_initiale = (volume_commande + volume_couverture) * facteur
st.markdown(f"💧 (Vw,sto,1)**Volume de initiale du chauffeau* : {volume_initiale:.2f} l ")
st.markdown("---")



# Ajout du champ pour le volume réel ou commercialisé
volume_reel = st.number_input(
    "Volume normalisé du chauffeau (l)",
    min_value=300, value=1000, step=1, format="%d"
)
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
perte_limite = interpolation_lineaire(volume_reel, volumes, pertes_limites)
 # Ajout du champ pour le nombre de raccordements hydrauliques
c2 = st.number_input(
    "Nombre de raccordements hydrauliques au accumulateur ECS",
    min_value=2, value=2, step=1, format="%d"
)
# Calcul des pertes thermiques du accumulateur
if c2 > 2:
    pertes_raccordement = (c2 - 2) * 0.11
else:
    pertes_raccordement = 0.0

Qw_sto_is = perte_limite + pertes_raccordement
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
Qw = volume_reel * 0.00116 * (t_max - t_min)
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
# Boutons d'action
# -----------------------

st.markdown("### Actions")
col_button1, col_button2 = st.columns(2)

with col_button1:
    calculer = st.button("🧮 Calculer les résultats")
with col_button2:
    export_pdf = st.button("📄 Exporter les résultats en PDF")

# -----------------------
# Calcul des résultats
# -----------------------

if calculer:
    # Calcul des résultats principaux
    total_personnes_npi = sum(
        appartements[typologie] * typologie_occupants[typologie]
        for typologie in typologie_occupants
    )
    volume_utile = total_personnes_npi * litres_par_personne_Vwui
    delta_t = t_max - t_min  # Calcul de l'écart de température
    puissance_kw = (volume_utile * cp * delta_t) / (temps_chauffe * 3600 * cycles)

    # Affichage des résultats
    st.markdown("### ✅ Résultats")
    st.success(f"👥 **Nombre total de personnes :** `{total_personnes_npi:.1f}`")
    st.info(f"💧 **Volume du accumulateur :** `{volume_reel:.1f} L`")
    st.info(f"💧 **Cycles :** `{cycles:.1f} Cycles par jour`")
    st.warning(f"⚡ **Puissance thermique nécessaire :** `{Qw_gen_out:.2f} kW`")

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
            <li><strong>Nombre de personnes :</strong> {total_personnes_npi:.1f}</li>
            <li><strong>Volume d'eau chaude :</strong> {volume_utile:.1f} L</li>
            <li><strong>Puissance thermique :</strong> {puissance_kw:.2f} kW</li>
            <li><strong>ΔT :</strong> {delta_t} °C</li>
        </ul>
    </body>
    </html>
    """

# -----------------------
# Export des résultats en PDF
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
        st.warning("Veuillez d'abord ef fectuer un calcul pour exporter les résultats.")

# Export PDF
# -----------------------


    import json

# Bouton pour exporter les variables d'entrée
if st.button("📤 Exporter les variables d'entrée"):
    # Récupérer les variables d'entrée
    variables_entree = {
        "appartements": {typologie: int(appartements[typologie]) for typologie in appartements},
        "litres_par_personne_Vwui": float(litres_par_personne_Vwui),
        "t_min": float(t_min),
        "t_max": float(t_max),
        "cycles": int(cycles),
        "temps_chauffe": int(temps_chauffe),
        "volume_reel": int(volume_reel),
        "c2": int(c2)
    }

    st.download_button("📁 Télécharger les données JSON",
        data=json.dumps(variables_entree, indent=4),
        file_name="parametres_entree.json",
        mime="application/json"
    )


    # Convertir les données en JSON
    json_data = json.dumps(variables_entree, indent=4)

    # Bouton pour télécharger le fichier JSON
    st.download_button(
        label="⬇️ Télécharger les variables d'entrée",
        data=json_data,
        file_name="variables_entree.json",
        mime="application/json"
    )

# Bouton pour importer les variables d'entrée
uploaded_file = st.file_uploader("📥 Importer les variables d'entrée", type=["json"])
if uploaded_file is not None:
    try:
        # Charger les données depuis le fichier JSON
        variables_entree = json.load(uploaded_file)

        # Réassigner les valeurs aux variables
        appartements = variables_entree["appartements"]
        litres_par_personne_Vwui = variables_entree["litres_par_personne_Vwui"]
        t_min = variables_entree["t_min"]
        t_max = variables_entree["t_max"]
        cycles = variables_entree["cycles"]
        temps_chauffe = variables_entree["temps_chauffe"]
        volume_reel = variables_entree["volume_reel"]
        c2 = variables_entree["c2"]

        st.success("✅ Les variables d'entrée ont été importées avec succès.")
    except Exception as e:
        st.error(f"❌ Une erreur est survenue lors de l'importation : {e}")
