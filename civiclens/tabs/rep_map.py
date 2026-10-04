"""Rep Map: district boundaries colored by party, with governor and senator overlays."""
import re

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

from civiclens.data.congress import get_federal_house_members, get_federal_senators
from civiclens.data.geocode import geocode
from civiclens.data.governors import get_governor, governor_links_html
from civiclens.data.openstates import get_state_reps_by_chamber
from civiclens.data.tiger import (LAYER_STATE_HOUSE, LAYER_STATE_SENATE, LAYER_US_HOUSE,
                                  US_STATES_GEOJSON_URL, extract_district_key,
                                  fetch_tiger_geojson)
from civiclens.helpers import (address_input, build_rep_lookup, esc, get_chamber_label,
                               html_block, party_color, party_fill, party_label,
                               show_searched_address)
from civiclens.i18n import t
from civiclens.states import DEFAULT_STATE, STATES

def build_district_layer(geojson: dict, rep_lookup: dict, layer_name: str,
                         district_field: str = "") -> folium.FeatureGroup:
    fg = folium.FeatureGroup(name=layer_name, show=True)
    if not geojson or "features" not in geojson:
        return fg
    for feature in geojson["features"]:
        props     = feature.get("properties", {})
        dist_key  = extract_district_key(props, district_field)
        rep       = rep_lookup.get(dist_key, {})
        rep_name  = rep.get("name", t("No data"))
        rep_party = rep.get("party", "Unknown")
        rep_label = get_chamber_label(rep) if rep else ""
        rep_photo = rep.get("image", "")
        district  = t("District {district}", district=dist_key)
        fill, opacity = party_fill(rep_party)
        photo_html = (f"<img src='{esc(rep_photo)}' alt='{esc(rep_name)}' width='55' "
                      f"style='border-radius:50%;float:right;margin-left:8px'/>" if rep_photo else "")
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;padding:4px">
            {photo_html}
            <strong style="font-size:13px">{esc(district)}</strong><br>
            <strong>{esc(rep_name)}</strong><br>
            <em style="color:#555;font-size:12px">{esc(rep_label)}</em><br>
            <span style="color:{party_color(rep_party)};font-weight:600">{esc(party_label(rep_party))}</span>
        </div>"""
        try:
            folium.GeoJson(
                feature,
                style_function=lambda f, fill=fill, opacity=opacity: {
                    "fillColor": fill, "fillOpacity": opacity, "color": "#333", "weight": 1.2,
                },
                highlight_function=lambda f, fill=fill: {
                    "fillColor": fill, "fillOpacity": 0.45, "color": "#333", "weight": 2,
                },
                tooltip=esc(f"{district} — {rep_name} ({party_label(rep_party)})"),
                popup=folium.Popup(popup_html, max_width=260),
            ).add_to(fg)
        except Exception:
            pass
    return fg


def render():
    st.header(t("🗺️ District Map"))
    st.caption(t("Real district boundaries from the U.S. Census Bureau, colored by party. Click any district for rep details."))

    if st.button(t("🔄 Clear map cache"), help=t("Force re-fetch boundaries from Census — use if districts look wrong")):
        st.cache_data.clear()
        st.success(t("Cache cleared — click Show Map to reload."))

    col_addr, col_state = st.columns([3, 1])
    with col_addr:
        address = address_input(t("Enter your address (optional — pins your location and auto-selects the state below)"))
    with col_state:
        state_abbrs = sorted(STATES.keys())
        manual_state = st.selectbox(
            t("State"), state_abbrs,
            index=state_abbrs.index(DEFAULT_STATE),
            help=t("Auto-overridden if your address above resolves to a different state."),
        )

    st.markdown(f"**{t('Show district layer:')}**")
    col1, col2, col3, col4, col5 = st.columns(5)
    # DC has a Mayor, not a Governor. An address below can still override the dropdown,
    # in which case the layer name and popup follow the address's state.
    with col1: show_gov         = st.checkbox(t("Mayor") if manual_state == "DC" else t("Governor"), value=True)
    with col2: show_us_sen      = st.checkbox(t("U.S. Senate"), value=False)
    with col3: show_us_house    = st.checkbox(t("U.S. House"),  value=False)
    with col4: show_state_sen   = st.checkbox(t("State Senate"), value=False)
    with col5: show_state_house = st.checkbox(t("State House"),  value=False)

    if st.button(t("Show Map"), type="primary"):
        with st.status(t("Loading district data…"), expanded=True) as load_status:
            st.write(t("📡 Geocoding address…"))
            lat, lng, detected_state = None, None, None
            if address.strip():
                lat, lng, detected_state = geocode(address)

            # Address-detected state wins; otherwise fall back to the manual picker.
            state_abbr = detected_state or manual_state
            state_info = STATES.get(state_abbr, STATES[DEFAULT_STATE])
            state_fips = state_info["fips"]
            state_name = state_info["name"]   # English — used to match the outline file
            state_disp = t(state_name)
            if detected_state and detected_state != manual_state:
                st.write(t("📍 Address resolved to **{state}** — using that state.", state=state_disp))

            st.write(t("🗺️ Fetching Census district boundaries for {state}…", state=state_disp))
            geojson_us_house,     us_house_geo_err     = fetch_tiger_geojson(LAYER_US_HOUSE, state_fips, state_abbr)     if show_us_house    else ({}, "")
            geojson_state_senate, state_senate_geo_err = fetch_tiger_geojson(LAYER_STATE_SENATE, state_fips, state_abbr) if show_state_sen   else ({}, "")
            geojson_state_house,  state_house_geo_err  = fetch_tiger_geojson(LAYER_STATE_HOUSE, state_fips, state_abbr)  if show_state_house else ({}, "")
            senate_layer = f"{t('State Senate')} — {state_disp}"
            house_layer  = f"{t('State House')} — {state_disp}"
            boundary_errors = [
                (label, layer_id, err) for label, layer_id, err in [
                    (t("U.S. House"), LAYER_US_HOUSE,     us_house_geo_err),
                    (senate_layer,    LAYER_STATE_SENATE, state_senate_geo_err),
                    (house_layer,     LAYER_STATE_HOUSE,  state_house_geo_err),
                ] if err
            ]

            st.write(t("👥 Loading representative data…"))
            # A failed roster load is reported below as a missing-names warning
            state_senate_reps, _ = get_state_reps_by_chamber(state_abbr, "upper") if show_state_sen   else ([], "")
            state_house_reps,  _ = get_state_reps_by_chamber(state_abbr, "lower") if show_state_house else ([], "")
            us_house_reps  = get_federal_house_members(state_abbr) if show_us_house else []
            us_senators    = get_federal_senators(state_abbr)      if show_us_sen   else []
            governor, governor_err = get_governor(state_abbr) if show_gov else (None, "")
            gov_office = t("Mayor") if state_abbr == "DC" else t("Governor")

            lookup_state_senate = build_rep_lookup(state_senate_reps)
            lookup_state_house  = build_rep_lookup(state_house_reps)
            lookup_us_house     = build_rep_lookup(us_house_reps)
            if boundary_errors:
                load_status.update(label=t("⚠️ Map loaded with errors — see below"), state="error", expanded=False)
            else:
                load_status.update(label=t("✅ Map data loaded!"), state="complete", expanded=False)

        # Surface boundary failures outside the status box so they aren't hidden when it collapses
        for label, layer_id, err in boundary_errors:
            st.warning(t("⚠️ Could not load {label} district boundaries (TIGERweb layer {layer}). Last error: {err}. Click Show Map to retry. If this keeps happening, the Census TIGERweb layer IDs may have shifted again — check: tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Legislative/MapServer",
                         label=label, layer=layer_id, err=err))

        # Surface rep-load failures (st.warning not allowed inside cached functions)
        if show_state_sen and not state_senate_reps:
            st.warning(t("⚠️ Could not load {chamber} representatives. Boundaries will show without rep names.", chamber=senate_layer))
        if show_state_house and not state_house_reps:
            st.warning(t("⚠️ Could not load {chamber} representatives. Boundaries will show without rep names.", chamber=house_layer))
        if show_us_house and not us_house_reps:
            st.warning(t("⚠️ Could not load {chamber} representatives. Boundaries will show without rep names.", chamber=t("U.S. House")))
        if show_us_sen and not us_senators and state_abbr != "DC":
            st.warning(t("⚠️ Could not load U.S. Senators. The Senate overlay will show without names."))
        if show_gov and governor_err:
            st.warning(t("⚠️ Could not load the current {office} — {err}. The overlay will show without a name.",
                         office=gov_office.lower(), err=governor_err))

        show_searched_address(address)

        if lat:
            center, zoom = [lat, lng], 11
        else:
            # No address given — center on the selected state instead of always NC.
            fallback_lat, fallback_lng, _ = geocode(f"{state_name}, USA")
            center = [fallback_lat, fallback_lng] if fallback_lat else [35.5, -79.5]
            zoom = 7
        # OpenStreetMap's standard tiles need no key. (CARTO's free basemaps now serve an
        # "API KEY REQUIRED" watermark instead of a map.)
        m = folium.Map(location=center, zoom_start=zoom, tiles=None)
        folium.TileLayer("OpenStreetMap", name=t("Street map")).add_to(m)

        # Fetch the selected state's outline once and reuse for both Governor and US Senate overlays.
        # Using a stable GitHub-hosted GeoJSON instead of the shifting TIGERweb State_County layer.
        state_outline_geo = None
        if show_gov or show_us_sen:
            try:
                all_states_geo = requests.get(US_STATES_GEOJSON_URL, timeout=15).json()
                state_feature = next(
                    (f for f in all_states_geo.get("features", [])
                     if f.get("properties", {}).get("name") == state_name),
                    None
                )
                if state_feature:
                    state_outline_geo = {"type": "FeatureCollection", "features": [state_feature]}
            except Exception:
                pass

        # Governor/Mayor and U.S. Senate overlays are looked up live for every state.
        # If a lookup fails we still draw the outline, but say so in the popup instead
        # of showing a name we aren't sure about.
        if show_gov:
            try:
                gov_fg = folium.FeatureGroup(name=gov_office, show=True)
                office_of_state = t("{office} of {state}", office=gov_office, state=state_disp)
                if governor:
                    gov_photo_html = (
                        f"<img src='{esc(governor['photo'])}' alt='{esc(governor['name'])}' width='45' "
                        f"style='border-radius:50%;float:right;margin-left:8px'/>"
                        if governor["photo"] else ""
                    )
                    popup_html = html_block(f"""
                    <div style="font-family:sans-serif;min-width:200px">
                        {gov_photo_html}
                        <strong>{esc(governor['name'])}</strong><br>
                        <em style="color:#555">{esc(office_of_state)}</em><br>
                        <span style="color:{party_color(governor['party'])};font-weight:600">{esc(party_label(governor['party']))}</span><br>
                        {governor_links_html(governor)}
                    </div>""")
                    tooltip = esc(f"{gov_office}: {governor['name']} ({party_label(governor['party'])})")
                else:
                    popup_html = html_block(f"""
                    <div style="font-family:sans-serif;min-width:200px">
                        <strong>{esc(office_of_state)}</strong><br>
                        <span style="color:#888;font-size:0.85rem">{t("Could not load the current {office} right now.", office=gov_office.lower())}</span>
                    </div>""")
                    tooltip = esc(office_of_state)
                for feature in (state_outline_geo or {}).get("features", []):
                    folium.GeoJson(
                        feature,
                        style_function=lambda f: {"fillColor": "#1a73e8", "fillOpacity": 0.08, "color": "#1a73e8", "weight": 2, "dashArray": "6 4"},
                        highlight_function=lambda f: {"fillColor": "#1a73e8", "fillOpacity": 0.20, "color": "#1a73e8", "weight": 2, "dashArray": "6 4"},
                        tooltip=tooltip,
                        popup=folium.Popup(popup_html, max_width=260),
                    ).add_to(gov_fg)
                gov_fg.add_to(m)
            except Exception:
                pass

        if show_us_sen:
            try:
                sen_fg = folium.FeatureGroup(name=t("U.S. Senate"), show=True)
                senators_title = t("U.S. Senators for {state}", state=state_disp)
                if us_senators:
                    senator_blocks = ""
                    for senator in us_senators:
                        site_html = ""
                        if senator["url"]:
                            host = re.sub(r"^https?://(www\.)?", "", senator["url"]).rstrip("/")
                            site_html = f"<a href='{esc(senator['url'])}' target='_blank'>{esc(host)}</a><br>"
                        photo_html = (
                            f"<img src='{esc(senator['image'])}' alt='{esc(senator['name'])}' width='45' "
                            f"style='border-radius:50%;margin-right:6px'/>"
                            if senator["image"] else ""
                        )
                        senator_blocks += (
                            f"{photo_html}<strong>{esc(senator['name'])}</strong> "
                            f"<span style=\"color:{party_color(senator['party'])}\">{esc(party_label(senator['party']))}</span><br>"
                            f"{site_html}<br>"
                        )
                    popup_html = html_block(f"""
                    <div style="font-family:sans-serif;min-width:210px">
                        <strong>{esc(senators_title)}</strong><br><br>
                        {senator_blocks}
                    </div>""")
                    tooltip = esc(f"{t('U.S. Senators')}: " + " & ".join(
                        f"{s['name']} ({party_label(s['party'])[:1]})" for s in us_senators
                    ))
                else:
                    no_senators = state_abbr == "DC"
                    detail = (t("The District of Columbia has no voting U.S. Senators.")
                              if no_senators else
                              t("Could not load this state's U.S. Senators right now."))
                    popup_html = html_block(f"""
                    <div style="font-family:sans-serif;min-width:210px">
                        <strong>{esc(senators_title)}</strong><br>
                        <span style="color:#888;font-size:0.85rem">{detail}</span>
                    </div>""")
                    tooltip = esc(senators_title)
                for feature in (state_outline_geo or {}).get("features", []):
                    folium.GeoJson(
                        feature,
                        style_function=lambda f: {"fillColor": "#c0392b", "fillOpacity": 0.08, "color": "#c0392b", "weight": 2, "dashArray": "6 4"},
                        highlight_function=lambda f: {"fillColor": "#c0392b", "fillOpacity": 0.20, "color": "#c0392b", "weight": 2, "dashArray": "6 4"},
                        tooltip=tooltip,
                        popup=folium.Popup(popup_html, max_width=260),
                    ).add_to(sen_fg)
                sen_fg.add_to(m)
            except Exception:
                pass

        if show_us_house and geojson_us_house:
            build_district_layer(geojson_us_house, lookup_us_house, t("U.S. House"), district_field="CD119").add_to(m)
        if show_state_sen and geojson_state_senate:
            build_district_layer(geojson_state_senate, lookup_state_senate, senate_layer, district_field="SLDU").add_to(m)
        if show_state_house and geojson_state_house:
            build_district_layer(geojson_state_house, lookup_state_house, house_layer, district_field="SLDL").add_to(m)

        if lat:
            folium.Marker(
                location=[lat, lng], popup=t("📍 Your Address"), tooltip=t("You are here"),
                icon=folium.Icon(color="black", icon="home", prefix="fa"),
            ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        st.markdown(f"""
        <div class="map-legend">
            <strong style="font-size:0.85rem">{t("Party Key:")}</strong>
            <div class="legend-item"><span class="legend-dot" style="background:#1a73e8"></span> {t("Democrat")}</div>
            <div class="legend-item"><span class="legend-dot" style="background:#c0392b"></span> {t("Republican")}</div>
            <div class="legend-item"><span class="legend-dot" style="background:#888"></span> {t("Other / Unknown")}</div>
            <span style="font-size:0.78rem;color:var(--cl-muted);margin-left:auto">{t("Click any district for rep details")}</span>
        </div>
        """, unsafe_allow_html=True)
        # Fill the column instead of a fixed width, so the map fits on phones
        st_folium(m, use_container_width=True, height=580, returned_objects=[])
        st.caption(t("District boundaries: U.S. Census Bureau TIGERweb · State legislators: OpenStates API · Congress: unitedstates/congress-legislators · Governors: Wikidata"))
