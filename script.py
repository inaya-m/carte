import geopandas as gpd
import folium

# 1. Charger le fichier
fichier = "geom.geojson"
gdf = gpd.read_file(fichier)

print("Colonnes :", gdf.columns.tolist())
print("CRS lu :", gdf.crs)
print("Bornes initiales :", gdf.total_bounds)

# 2. Corriger le CRS (Lambert 93 -> WGS84)
gdf = gdf.set_crs(epsg=2154, allow_override=True)
gdf = gdf.to_crs(epsg=4326)

print("CRS final :", gdf.crs)
print("Bornes finales :", gdf.total_bounds)

# 3. Nettoyage simple
gdf = gdf[gdf.geometry.notnull()].copy()
gdf = gdf[gdf.is_valid].copy()

# 4. Créer la carte (centre sur la zone d'étude)
m = folium.Map(
    location=[48.9125, 2.3845],
    zoom_start=14.5,
    tiles=None
)
folium.TileLayer(
    tiles = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr = '&copy; <a href="https://www.openstreetmap.org/copyright" >Openstreet</a> contributors',
    name = "OSM couleur"
).add_to(m)

folium.TileLayer("CartoDB positron", name="Fond épuré").add_to(m)

# 5. Préparer les champs à afficher dans la popup
champs_popup = [
    "202603_NOM_OPE",
    "NATURE",
    "ADRESSE",
    "202603_ETAPES",
    "Calendrier_PU_QUART",
    "Calendrier_PU_PERIM",
    "Calendrier_PU_LIVR_PREV",
    "Calendrier_PU_NOM_MOA",
    "Calendrier_PU_NOM_MOE",
    "Calendrier_PU_NUM_ADS",
    "Calendrier_PU_VOC_DOM"
]
champs_popup = [c for c in champs_popup if c in gdf.columns]

alias_dict = {
    "202603_NOM_OPE": "Nom du projet",
    "NATURE": "Nature",
    "ADRESSE": "Adresse",
    "202603_ETAPES": "Étape",
    "Calendrier_PU_QUART": "Quartier",
    "Calendrier_PU_PERIM": "Périmètre",
    "Calendrier_PU_LIVR_PREV": "Livraison prévue",
    "Calendrier_PU_NOM_MOA": "MOA",
    "Calendrier_PU_NOM_MOE": "MOE",
    "Calendrier_PU_NUM_ADS": "N° PC",
    "Calendrier_PU_VOC_DOM": "Vocation dominante"
}
aliases = [alias_dict.get(c, c) for c in champs_popup]

# Couleurs par vocation dominante
couleurs_vocation = {
    "LOGEMENT": "#6bb8e3",
    "EQUIPEMENT": "#ff5466",
    "ESPACE PUBLIC": "#ffd940",
    "ACTIVITE": "#3d4e99",
    "BUREAU": "#ff8c40",
    "ESPACE VERT PUBLIC": "#b2e354",
    "ESPACE VERT PRIVE": "#70a182"
}
couleur_defaut = "#999999"
champ_vocation = "Calendrier_PU_VOC_DOM"

def highlight_projets(feature):
    return {
        "fillColor": "#ffff99",
        "color": "#000000",
        "weight": 3,
        "fillOpacity": 0.75
    }

# =========================
# 7. COUCHES PAR VOCATION
# =========================

valeurs_vocation = sorted(gdf[champ_vocation].dropna().unique())

for voc in valeurs_vocation:
    sous = gdf[gdf[champ_vocation] == voc].copy()
    if sous.empty:
        continue

    fg_voc = folium.FeatureGroup(name=f"Vocation : {voc}", show=True)

    def style_projets_voc(feature, voc=voc):
        vocation = feature["properties"].get(champ_vocation, None)
        couleur = couleurs_vocation.get(vocation, couleur_defaut)
        return {
            "fillColor": couleur,
            "color": "#333333",
            "weight": 2,
            "fillOpacity": 0.55
        }

    folium.GeoJson(
        sous,
        name=f"Projets {voc}",
        style_function=style_projets_voc,
        highlight_function=highlight_projets,
        tooltip=folium.GeoJsonTooltip(
            fields=["202603_NOM_OPE"] if "202603_NOM_OPE" in sous.columns else ["OBJECTID"],
            aliases=["Projet :"],
            localize=True,
            sticky=False,
            labels=True
        ),
        popup=folium.GeoJsonPopup(
            fields=champs_popup,
            aliases=aliases,
            localize=True,
            labels=True,
            max_width=300
        )
    ).add_to(fg_voc)

    fg_voc.add_to(m)

# =======================
# 8. COUCHES PAR ÉTAPE
# =======================

champ_etape = "202603_ETAPES"
valeurs_etapes = sorted(gdf[champ_etape].dropna().unique())

for etape in valeurs_etapes:
    sous = gdf[gdf[champ_etape] == etape].copy()
    if sous.empty:
        continue

    fg_etape = folium.FeatureGroup(name=f"Étape : {etape}", show=False)

    def style_projets_etape(feature):
        # couleur toujours par vocation
        vocation = feature["properties"].get(champ_vocation, None)
        couleur = couleurs_vocation.get(vocation, couleur_defaut)
        return {
            "fillColor": couleur,
            "color": "#333333",
            "weight": 2,
            "fillOpacity": 0.55
        }

    folium.GeoJson(
        sous,
        name=f"Projets {etape}",
        style_function=style_projets_etape,
        highlight_function=highlight_projets,
        tooltip=folium.GeoJsonTooltip(
            fields=["202603_NOM_OPE"] if "202603_NOM_OPE" in sous.columns else ["OBJECTID"],
            aliases=["Projet :"],
            localize=True,
            sticky=False,
            labels=True
        ),
        popup=folium.GeoJsonPopup(
            fields=champs_popup,
            aliases=aliases,
            localize=True,
            labels=True,
            max_width=300
        )
    ).add_to(fg_etape)

    fg_etape.add_to(m)

# 9. Contrôle de couche
folium.LayerControl(collapsed=True).add_to(m)

# 9bis. Bandeau titre avec logo à droite
titre_html = '''
<div style="
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 9999;
    background-color: rgba(255, 255, 255, 0.97);
    border-bottom: 2px solid grey;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    padding: 10px 20px;
    font-family: Arial, sans-serif;
">
    <div style="
        position: relative;
        width: 100%;
        text-align: center;
    ">
        <span style="
            font-size: 22px;
            font-weight: bold;
            color: #222;
        ">
            Carte interactive des projets d'aménagement
        </span>
        <img 
            src="https://upload.wikimedia.org/wikipedia/commons/5/5e/Logo_Aubervilliers.png"
            alt="Logo de la Ville d'Aubervilliers"
            style="
                height: 42px;
                position: absolute;
                right: 10px;
                top: 50%;
                transform: translateY(-50%);
            "
        >
    </div>
</div>
'''
m.get_root().html.add_child(folium.Element(titre_html))

# 9ter. Décaler les contrôles vers le bas
css_controles = '''
<style>
.leaflet-top {
    top: 55px !important;
}
</style>
'''
m.get_root().html.add_child(folium.Element(css_controles))

# 9quater. Légende HTML en bas à gauche
legende_html = '''
<div style="
    position: fixed; 
    bottom: 20px; 
    left: 20px; 
    width: 240px; 
    background-color: rgba(255, 255, 255, 0.95);
    border: 2px solid grey;
    z-index: 9999;
    font-size: 14px;
    padding: 12px;
    border-radius: 6px;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
    font-family: Arial, sans-serif;
">
    <b>Vocation dominante</b><br><br>
    <i style="background:#6bb8e3; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Logement<br>
    <i style="background:#ff5466; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Équipement<br>
    <i style="background:#ffd940; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Espace public<br>
    <i style="background:#3d4e99; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Activité<br>
    <i style="background:#ff8c40; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Bureau<br>
    <i style="background:#b2e354; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Espace vert public<br>
    <i style="background:#70a182; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Espace vert privé<br>
    <i style="background:#999999; width:14px; height:14px; display:inline-block; margin-right:8px;"></i>Autre / non renseigné
</div>
'''
m.get_root().html.add_child(folium.Element(legende_html))

credit_html = '''
<div style="
    position: fixed;
    bottom: 12px;
    right: 0px;
    z-index: 9999;
    font-family: Arial, sans-serif;
    font-size: 10px;
    color: #555;
    background-color: rgba(255, 255, 255, 0.8);
    padding: 2px 6px;
    border-radius: 3px;
">
    Réalisation : © Inaya MAGHOO, 2026
</div>
'''
m.get_root().html.add_child(folium.Element(credit_html))
# 10. Sauvegarde
m.save("carte_projets_aubervilliers_im.html")
print("Carte créée : carte_projets_aubervilliers_im.html")