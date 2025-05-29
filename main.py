import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Acoustique des Tuyaux", layout="wide")

st.title("Calcul de fréquence acoustique dans un tuyau")

st.markdown("""
Cette application permet de calculer les fréquences sonores produites par un écoulement d'air dans un tuyau,
en fonction de différents paramètres physiques et géométriques, incluant l'effet des trous latéraux.
""")

# Sidebar pour les paramètres
st.sidebar.header("Paramètres du tuyau")

# Paramètres géométriques (en mm)
col1, col2 = st.sidebar.columns(2)
with col1:
    longueur_mm = st.number_input("Longueur (mm)", min_value=100, max_value=10000, value=1000, step=10)
    longueur = longueur_mm / 1000  # Conversion en mètres
with col2:
    diametre_mm = st.number_input("Diamètre (mm)", min_value=5, max_value=500, value=50, step=1)
    diametre = diametre_mm / 1000  # Conversion en mètres

# Paramètres de l'écoulement (en km/h)
vitesse_kmh = st.sidebar.slider("Vitesse de l'air (km/h)", min_value=1, max_value=180, value=36, step=1)
vitesse_air = vitesse_kmh / 3.6  # Conversion en m/s
temperature = st.sidebar.slider("Température (°C)", min_value=-20, max_value=50, value=20, step=1)

# Configuration du tuyau
type_tuyau = st.sidebar.radio("Type de tuyau", ["Ouvert aux deux extrémités", "Fermé à une extrémité"])

# Gestion des trous latéraux
st.sidebar.header("Trous latéraux")
nb_trous = st.sidebar.number_input("Nombre de trous", min_value=0, max_value=10, value=0, step=1)

trous = []
if nb_trous > 0:
    st.sidebar.markdown("### Configuration des trous")
    for i in range(nb_trous):
        st.sidebar.markdown(f"#### Trou {i+1}")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            pos_trou = st.number_input(f"Position (% longueur)", key=f"pos_trou_{i}", 
                                       min_value=5.0, max_value=95.0, value=25.0 + i*10, step=5.0)
        with col2:
            diam_trou_mm = st.number_input(f"Diamètre (mm)", key=f"diam_trou_{i}", 
                                         min_value=1.0, max_value=float(diametre_mm-1), value=min(10.0, diametre_mm/3), step=0.5)
        
        trous.append({
            "position": pos_trou / 100,  # Convertir en fraction de la longueur
            "diametre": diam_trou_mm / 1000  # Convertir en mètres
        })

# Calculer la vitesse du son en fonction de la température
vitesse_son = 331.3 * np.sqrt(1 + temperature / 273.15)  # m/s

# Calcul des fréquences
def calculer_frequence_fondamentale(v_son, L, type_tube):
    if type_tube == "Ouvert aux deux extrémités":
        return v_son / (2 * L)
    else:  # Fermé à une extrémité
        return v_son / (4 * L)

def calculer_harmoniques(freq_fond, nombre_harmoniques, type_tube):
    if type_tube == "Ouvert aux deux extrémités":
        return [freq_fond * (n + 1) for n in range(nombre_harmoniques)]
    else:  # Fermé à une extrémité (harmoniques impaires seulement)
        return [freq_fond * (2 * n + 1) for n in range(nombre_harmoniques)]

def calculer_frequence_avec_trous(v_son, L, type_tube, trous, diametre_tube):
    if not trous:
        return calculer_frequence_fondamentale(v_son, L, type_tube)
    
    # Tri des trous par position (du plus proche de l'embouchure au plus éloigné)
    trous_tries = sorted(trous, key=lambda t: t["position"])
    
    # Position du premier trou (en mètres depuis l'embouchure)
    position_premier_trou = trous_tries[0]["position"] * L
    diametre_premier_trou = trous_tries[0]["diametre"]
    
    # Correction de longueur basée sur le diamètre du trou
    correction = 0.3 * diametre_premier_trou
    
    # Pour trous multiples, considérer leur influence globale
    if len(trous) > 1:
        correction_multi = 0
        section_tube = np.pi * (diametre_tube/2)**2
        
        for trou in trous_tries:
            section_trou = np.pi * (trou["diametre"]/2)**2
            correction_multi += (section_trou / section_tube) * (1 - trou["position"]) * L * 0.1
        
        correction += correction_multi
    
    # Longueur effective jusqu'au premier trou + correction
    longueur_effective = position_premier_trou + correction
    
    if type_tube == "Ouvert aux deux extrémités":
        return v_son / (2 * longueur_effective)
    else:  # Fermé à une extrémité
        return v_son / (4 * longueur_effective)

# Calculer les valeurs
if nb_trous > 0:
    freq_fondamentale = calculer_frequence_avec_trous(vitesse_son, longueur, type_tuyau, trous, diametre)
else:
    freq_fondamentale = calculer_frequence_fondamentale(vitesse_son, longueur, type_tuyau)

harmoniques = calculer_harmoniques(freq_fondamentale, 5, type_tuyau)

# Afficher les résultats
col1, col2 = st.columns(2)

with col1:
    st.subheader("Paramètres acoustiques")
    st.write(f"Vitesse du son à {temperature}°C: {vitesse_son:.2f} m/s")
    
    if nb_trous > 0:
        st.write(f"Fréquence fondamentale (avec trous): {freq_fondamentale:.2f} Hz")
        # Calculer aussi la fréquence sans trous pour comparaison
        freq_sans_trous = calculer_frequence_fondamentale(vitesse_son, longueur, type_tuyau)
        st.write(f"Fréquence fondamentale (sans trous): {freq_sans_trous:.2f} Hz")
        st.write(f"Différence: {freq_fondamentale - freq_sans_trous:.2f} Hz")
    else:
        st.write(f"Fréquence fondamentale: {freq_fondamentale:.2f} Hz")
    
    st.write("Harmoniques:")
    for i, freq in enumerate(harmoniques):
        st.write(f"   Harmonique {i+1}: {freq:.2f} Hz")

# Visualisation du tuyau en vertical avec Plotly
with col2:
    st.subheader("Visualisation du tuyau")
    
    # Créer une figure avec Plotly
    fig = go.Figure()
    
    # Paramètres pour la visualisation
    largeur_tuyau = diametre  # Largeur du tuyau en mètres
    
    # Dessiner le tuyau (rectangle vertical)
    fig.add_shape(
        type="rect",
        x0=-largeur_tuyau/2,
        y0=0,
        x1=largeur_tuyau/2,
        y1=longueur,
        line=dict(color="blue", width=2),
        fillcolor="rgba(0, 0, 255, 0.1)"
    )
    
    # Ajouter des indicateurs pour les extrémités
    if type_tuyau == "Ouvert aux deux extrémités":
        # Embouchure (entrée)
        fig.add_shape(
            type="circle",
            x0=-largeur_tuyau/2,
            y0=-largeur_tuyau/4,
            x1=largeur_tuyau/2,
            y1=largeur_tuyau/4,
            line=dict(color="green", width=1),
            fillcolor="rgba(0, 0, 0, 0)"
        )
        fig.add_annotation(
            x=-largeur_tuyau,
            y=0,
            text="Ouvert",
            showarrow=False,
            xanchor="right"
        )
        
        # Extrémité de sortie
        fig.add_shape(
            type="circle",
            x0=-largeur_tuyau/2,
            y0=longueur-largeur_tuyau/4,
            x1=largeur_tuyau/2,
            y1=longueur+largeur_tuyau/4,
            line=dict(color="green", width=1),
            fillcolor="rgba(0, 0, 0, 0)"
        )
        fig.add_annotation(
            x=-largeur_tuyau,
            y=longueur,
            text="Ouvert",
            showarrow=False,
            xanchor="right"
        )
    else:
        # Embouchure (entrée)
        fig.add_shape(
            type="circle",
            x0=-largeur_tuyau/2,
            y0=-largeur_tuyau/4,
            x1=largeur_tuyau/2,
            y1=largeur_tuyau/4,
            line=dict(color="green", width=1),
            fillcolor="rgba(0, 0, 0, 0)"
        )
        fig.add_annotation(
            x=-largeur_tuyau,
            y=0,
            text="Ouvert",
            showarrow=False,
            xanchor="right"
        )
        
        # Extrémité fermée
        fig.add_shape(
            type="rect",
            x0=-largeur_tuyau/2,
            y0=longueur,
            x1=largeur_tuyau/2,
            y1=longueur+largeur_tuyau/10,
            line=dict(color="gray", width=1),
            fillcolor="gray"
        )
        fig.add_annotation(
            x=-largeur_tuyau,
            y=longueur,
            text="Fermé",
            showarrow=False,
            xanchor="right"
        )
    
    # Indiquer l'écoulement d'air
    fig.add_annotation(
        x=0,
        y=largeur_tuyau,
        text=f"Air: {vitesse_kmh} km/h",
        showarrow=True,
        arrowhead=1,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="red",
        ax=0,
        ay=50
    )
    
    # Dessiner les trous
    for i, trou in enumerate(trous):
        trou_y = longueur * trou["position"]
        trou_diametre = trou["diametre"]
        
        # Dessiner le trou (cercle)
        fig.add_shape(
            type="circle",
            x0=largeur_tuyau/2 - trou_diametre/10,
            y0=trou_y - trou_diametre/2,
            x1=largeur_tuyau/2 + trou_diametre,
            y1=trou_y + trou_diametre/2,
            line=dict(color="black", width=1),
            fillcolor="white"
        )
        
        # Étiquette du trou
        fig.add_annotation(
            x=largeur_tuyau/2 + trou_diametre*1.5,
            y=trou_y,
            text=f"T{i+1}",
            showarrow=False
        )
    
    # Configuration de la mise en page
    fig.update_layout(
        showlegend=False,
        width=400,
        height=600,
        margin=dict(l=50, r=50, t=50, b=50),
        xaxis=dict(
            title="Diamètre (m)",
            range=[-largeur_tuyau*2, largeur_tuyau*3]
        ),
        yaxis=dict(
            title="Longueur (m)",
            range=[-0.2, longueur*1.1],
            scaleanchor="x",
            scaleratio=1
        ),
        plot_bgcolor="white"
    )
    
    st.plotly_chart(fig)

# Graphique de l'évolution de la fréquence
st.subheader("Évolution de la fréquence fondamentale")

# Paramètre à faire varier
options = ["Longueur", "Diamètre", "Vitesse de l'air", "Température"]
if nb_trous > 0:
    options.append("Position du premier trou")

param_variable = st.selectbox("Paramètre à faire varier", options)

if param_variable == "Longueur":
    x_values_mm = np.linspace(100, 10000, 100)
    x_values = x_values_mm / 1000  # Conversion en mètres
    if nb_trous > 0:
        y_values_fond = [calculer_frequence_avec_trous(vitesse_son, x, type_tuyau, 
                                                      [{**t, "position": t["position"] * longueur / x} for t in trous], 
                                                      diametre) for x in x_values]
    else:
        y_values_fond = [calculer_frequence_fondamentale(vitesse_son, x, type_tuyau) for x in x_values]
    x_label = "Longueur du tuyau (mm)"
    x_display = x_values_mm  # Afficher en mm
    
elif param_variable == "Diamètre":
    x_values_mm = np.linspace(5, 500, 100)
    x_values = x_values_mm / 1000  # Conversion en mètres
    if nb_trous > 0:
        y_values_fond = [calculer_frequence_avec_trous(vitesse_son, longueur, type_tuyau, trous, x) for x in x_values]
    else:
        y_values_fond = [calculer_frequence_fondamentale(vitesse_son, longueur, type_tuyau) for _ in x_values]
    x_label = "Diamètre du tuyau (mm)"
    x_display = x_values_mm  # Afficher en mm
    
elif param_variable == "Vitesse de l'air":
    x_values_kmh = np.linspace(1, 180, 100)  # km/h
    x_values = x_values_kmh / 3.6  # Conversion en m/s
    y_values_fond = [calculer_frequence_fondamentale(vitesse_son, longueur, type_tuyau) for _ in x_values]
    x_label = "Vitesse de l'air (km/h)"
    x_display = x_values_kmh  # Afficher en km/h
    
elif param_variable == "Température":
    x_values = np.linspace(-20, 50, 100)
    v_sons = [331.3 * np.sqrt(1 + t / 273.15) for t in x_values]
    if nb_trous > 0:
        y_values_fond = [calculer_frequence_avec_trous(v, longueur, type_tuyau, trous, diametre) for v in v_sons]
    else:
        y_values_fond = [calculer_frequence_fondamentale(v, longueur, type_tuyau) for v in v_sons]
    x_label = "Température (°C)"
    x_display = x_values  # Pas de conversion
    
elif param_variable == "Position du premier trou" and nb_trous > 0:
    x_values_percent = np.linspace(5, 95, 100)
    x_values = x_values_percent
    
    y_values_fond = []
    for pos in x_values_percent:
        # Créer une copie des trous avec le premier trou à différentes positions
        trous_modifies = trous.copy()
        trous_modifies[0]["position"] = pos / 100
        y_values_fond.append(calculer_frequence_avec_trous(vitesse_son, longueur, type_tuyau, trous_modifies, diametre))
    
    x_label = "Position du premier trou (% de la longueur)"
    x_display = x_values  # Pas de conversion

# Création du graphique d'évolution avec Plotly
fig = go.Figure()

# Tracer la courbe d'évolution
fig.add_trace(
    go.Scatter(
        x=x_display,
        y=y_values_fond,
        mode='lines',
        name='Fréquence fondamentale',
        line=dict(color='blue', width=2)
    )
)

# Marquer la valeur actuelle
if param_variable == "Longueur":
    current_x = longueur_mm
elif param_variable == "Diamètre":
    current_x = diametre_mm
elif param_variable == "Vitesse de l'air":
    current_x = vitesse_kmh
elif param_variable == "Température":
    current_x = temperature
elif param_variable == "Position du premier trou" and nb_trous > 0:
    current_x = trous[0]["position"] * 100

current_idx = np.abs(x_display - current_x).argmin()
current_y_fond = y_values_fond[current_idx]

fig.add_trace(
    go.Scatter(
        x=[current_x],
        y=[current_y_fond],
        mode='markers',
        marker=dict(color='blue', size=10),
        name='Valeur actuelle'
    )
)

fig.add_annotation(
    x=current_x,
    y=current_y_fond,
    text=f"{current_y_fond:.2f} Hz",
    showarrow=True,
    arrowhead=1,
    ax=40,
    ay=-40
)

# Configuration de la mise en page
fig.update_layout(
    xaxis_title=x_label,
    yaxis_title="Fréquence (Hz)",
    title=f"Évolution de la fréquence en fonction de {param_variable.lower()}",
    width=800,
    height=500,
    plot_bgcolor="white",
    hovermode="closest"
)

fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')
fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGrey')

st.plotly_chart(fig)

# Explication des formules
st.subheader("Formules utilisées")

st.markdown("""
### Fréquence fondamentale (sans trous)
- **Tuyau ouvert aux deux extrémités**: $f_0 = \\frac{v}{2L}$
- **Tuyau fermé à une extrémité**: $f_0 = \\frac{v}{4L}$

Où:
- $v$ est la vitesse du son dans l'air (m/s)
- $L$ est la longueur du tuyau (m)

### Fréquence fondamentale (avec trous)
La présence de trous modifie la longueur effective du tuyau:

$L_{eff} = L_1 + 0.3d$

Où:
- $L_1$ est la distance de l'embouchure au premier trou ouvert
- $d$ est le diamètre du trou
- $0.3d$ est la correction de longueur due au trou""")