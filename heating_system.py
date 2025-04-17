from PIL import Image  # Ajout de l'importation manquante
import streamlit as st
import pdfkit
import tempfile
import os


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
    st.title("📊 Dimensionnement du boiler – méthode fodass")

st.header("🏢 Typologie des appartements")
appartements = {}
for typologie in typologie_occupants:
    appartements[typologie] = st.number_input(f"Nombre d'appartements {typologie}", min_value=0, value=0, step=1, key=typologie)

st.header("👥 Besoin en eau chaude")
litres_par_personne = st.number_input("Litres d'eau chaude par personne", min_value=10, max_value=200, value=55)

st.header("♨️ Paramètres de chauffe")

col1, col2 = st.columns(2)
with col1:
    t_min = st.number_input("Température de l’eau froide (°C)", min_value=0, max_value=50, value=10)
with col2:
    t_max = st.number_input("Température de l’eau chaude souhaitée (°C)", min_value=40, max_value=80, value=60)

delta_t = t_max - t_min
st.markdown(f"🔺 **Élévation de température (ΔT)** : `{delta_t} °C`")

col3, col4 = st.columns(2)
with col3:
    cycles = st.number_input("Nombre de cycles par jour", min_value=1, value=2)
with col4:
    temps_chauffe = st.number_input("Temps de chauffe par cycle (en minutes)", min_value=10, value=60)

# -----------------------
# Boutons
# -----------------------

col_button1, col_button2, col_button3 = st.columns(3)

with col_button1:
    calculer = st.button("🧮 Calculer")
with col_button2:
    reset = st.button("🔄 Réinitialiser")
with col_button3:
    export_pdf = st.button("📄 Exporter en PDF")

# -----------------------
# Calcul
# -----------------------

if calculer:
    total_personnes = sum(appartements[typologie] * typologie_occupants[typologie] for typologie in typologie_occupants)
    volume_total = total_personnes * litres_par_personne
    temps_chauffe_sec = temps_chauffe * 60
    puissance_kw = (volume_total * cp * delta_t) / (temps_chauffe_sec * cycles)

    st.header("✅ Résultats")
    st.write(f"👥 Nombre total de personnes : **{total_personnes:.1f}**")
    st.write(f"💧 Volume total d’eau chaude requis : **{volume_total:.1f} L**")
    st.write(f"⚡ Puissance thermique nécessaire : **{puissance_kw:.2f} kW**")

    # Stockage des résultats pour PDF
    st.session_state["resultat_html"] = f"""
    <h2>Résultats</h2>
    <ul>
    <li><strong>Nombre de personnes :</strong> {total_personnes:.1f}</li>
    <li><strong>Volume d’eau chaude :</strong> {volume_total:.1f} L</li>
    <li><strong>Puissance thermique :</strong> {puissance_kw:.2f} kW</li>
    <li><strong>ΔT :</strong> {delta_t} °C</li>
    </ul>
    """

if reset:
    st.experimental_rerun()

# -----------------------
# Export PDF
# -----------------------

if export_pdf:
    if "resultat_html" in st.session_state:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            pdfkit.from_string(st.session_state["resultat_html"], f.name)
            st.success("📄 Résultat exporté avec succès.")
            with open(f.name, "rb") as file:
                st.download_button("⬇️ Télécharger le PDF", data=file, file_name="dimensionnement_boiler.pdf", mime="application/pdf")
            os.unlink(f.name)
    else:
        st.warning("Veuillez d'abord effectuer un calcul.")
