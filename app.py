        col_t1, col_t2 = st.columns(2)
        with col_t1:
            pct_propina = st.number_input(
                "Porcentaje de Propina (%):",
                min_value=0.0,
                max_value=100.0,
                value=18.0,
                step=1.0,
                format="%.1f"
            )
        with col_t2:
            base_calc = st.radio("Calcular propina sobre:", ["Subtotal sin tax", "Total con tax"])

        tax_rate = 0.0 if es_ropa_exenta else 0.08875
        tax_total = subtotal_bill * tax_rate
        base_tip = subtotal_bill if "Subtotal" in base_calc else (subtotal_bill + tax_total)
        tip_total = base_tip * (pct_propina / 100.0)
        gran_total = subtotal_bill + tax_total + tip_total
        gran_total_eur = gran_total * tasa_eur

        st.markdown(f"""
        <div class="ny-card" style="margin-top:10px; border: 1.5px solid #E2E8F0;">
          <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.88rem;">
            <span style="color:#0F172A;">Subtotal carta:</span>
            <b>${subtotal_bill:.2f}</b>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.88rem;">
            <span style="color:#0F172A;">NYC  Tax ({'Exenta' if es_ropa_exenta else '8.875%'}):</span>
            <b>{'Exenta ($0.00)' if es_ropa_exenta else f'${tax_total:.2f}'}</b>
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.88rem;">
            <span style="color:#0F172A;">Propina ({pct_propina:.1f}%):</span>
            <b>${tip_total:.2f}</b>
          </div>
          <div style="border-top:1.5px solid #E2E8F0; padding-top:10px; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:1.05rem; font-weight:800; color:#0F172A;">Total a Pagar:</span>
            <div style="text-align:right;">
              <span style="font-size:1.35rem; font-weight:800; color:#0F172A;">${gran_total:.2f} USD</span><br>
              <span style="font-size:0.84rem; color:#0F172A;">≈ {gran_total_eur:.2f} €</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        num_personas = 3
        st.markdown("**Dividir entre 3 personas**")
        per_p_usd = gran_total / num_personas
        per_p_eur = gran_total_eur / num_personas
        st.info(f"👉 **Por persona (3 personas):** **${per_p_usd:.2f} USD** (~ {per_p_eur:.2f} €)")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6: VUELOS, HOTEL & LISTAS
# ─────────────────────────────────────────────────────────────────────────────
def extraer_codigos_vuelo(texto_vuelo: str) -> list:
    return re.findall(r"\b([A-Z]{2}\d{2,4})\b", (texto_vuelo or "").upper())

with pestanas[4]:
    c_vl1, c_vl2 = st.columns(2)

    with c_vl1:
        st.markdown('<div class="ny-card-header">✈️ Vuelos & Estado en Tiempo Real</div>', unsafe_allow_html=True)

        cods_ida = extraer_codigos_vuelo(v_ida.get("vuelo", ""))
        cods_vta = extraer_codigos_vuelo(v_vta.get("vuelo", ""))

        st.markdown("""
        <div class="ny-card" style="border-left: 5px solid #2563EB; margin-bottom:10px;">
          <div style="font-weight:800; font-size:0.92rem; color:#0F172A; margin-bottom:4px;">📡 Seguimiento en Vivo (FlightAware / Flightradar24)</div>
          <div style="font-size:0.82rem; color:#0F172A;">Pulsa en el código de vuelo para ver terminal, puerta y retrasos:</div>
        </div>
        """, unsafe_allow_html=True)

        if cods_ida:
            st.markdown(f"**🛫 Ida ({v_ida.get('fecha', '26 Dic')} · {v_ida.get('hora', '15:30')}):**")
            for idx_c, cod in enumerate(cods_ida):
                fa_url = f"https://es.flightaware.com/live/flight/{cod}"
                fr_url = f"https://www.flightradar24.com/data/flights/{cod.lower()}"
                with st.container(key=f"flight-links-ida-{idx_c}-{cod.lower()}"):
                    st.markdown(f"<div style='font-weight:800; font-size:0.84rem; margin:4px 0;'>✈️ {html.escape(cod)}</div>", unsafe_allow_html=True)
                    fa_col, fr_col = st.columns(2, gap="small")
                    with fa_col:
                        st.link_button("FlightAware ↗", fa_url, use_container_width=True)
                    with fr_col:
                        st.link_button("Flightradar24 ↗", fr_url, use_container_width=True)

        if cods_vta:
            st.markdown(f"**🛬 Regreso ({v_vta.get('fecha', '4 Ene')} · {v_vta.get('hora', '20:45')}):**")
            for idx_c, cod in enumerate(cods_vta):
                fa_url = f"https://es.flightaware.com/live/flight/{cod}"
                fr_url = f"https://www.flightradar24.com/data/flights/{cod.lower()}"
                with st.container(key=f"flight-links-regreso-{idx_c}-{cod.lower()}"):
                    st.markdown(f"<div style='font-weight:800; font-size:0.84rem; margin:4px 0;'>✈️ {html.escape(cod)}</div>", unsafe_allow_html=True)
                    fa_col, fr_col = st.columns(2, gap="small")
                    with fa_col:
                        st.link_button("FlightAware ↗", fa_url, use_container_width=True)
                    with fr_col:
                        st.link_button("Flightradar24 ↗", fr_url, use_container_width=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.expander("✏️ Editar datos de vuelos", expanded=False):
            with st.form("form_editar_vuelos"):
                ida_v = st.text_input("Vuelo Ida (ej. Aer Lingus · EI583, EI107):", value=v_ida.get("vuelo", "Aer Lingus · EI583, EI107"))
                ida_f = st.text_input("Fecha Ida:", value=v_ida.get("fecha", "26 Dic"))
                ida_h = st.text_input("Hora Ida:", value=v_ida.get("hora", "15:30"))
                ida_a = st.text_input("Aeropuerto:", value=v_ida.get("aeropuerto", "JFK / Nueva York"))
                st.markdown("---")
                vta_v = st.text_input("Vuelo Regreso (ej. Aer Lingus · EI104, EI582):", value=v_vta.get("vuelo", "Aer Lingus · EI104, EI582"))
                vta_f = st.text_input("Fecha Regreso:", value=v_vta.get("fecha", "4 Ene"))
                vta_h = st.text_input("Hora Regreso:", value=v_vta.get("hora", "20:45"))
                vta_a = st.text_input("Aeropuerto Regreso:", value=v_vta.get("aeropuerto", "JFK / Nueva York"))
                if st.form_submit_button("💾 Guardar Vuelos"):
                    st.session_state.config_viaje["vuelo_ida"] = {"vuelo": ida_v, "fecha": ida_f, "hora": ida_h, "aeropuerto": ida_a}
                    st.session_state.config_viaje["vuelo_vuelta"] = {"vuelo": vta_v, "fecha": vta_f, "hora": vta_h, "aeropuerto": vta_a}
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.toast("Datos de vuelos actualizados.", icon="✈️")
                    st.rerun()

    with c_vl2:
        st.markdown('<div class="ny-card-header">🏨 Hotel</div>', unsafe_allow_html=True)

        hotel_nom_act = hotel.get("nombre", "Courtyard by Marriott New York Manhattan Upper East Side")
        hotel_dir_act = hotel.get("direccion", "410 E 92nd St, New York, NY 10128")
        hotel_lat_act = hotel.get("lat", 40.780242)
        hotel_lon_act = hotel.get("lon", -73.946123)

        gmaps_hotel_search = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(hotel_nom_act + ' ' + hotel_dir_act)}"
        gmaps_hotel_dir = f"https://www.google.com/maps/dir/?api=1&destination={hotel_lat_act},{hotel_lon_act}"

        st.markdown(f"""
        <div class="ny-card" style="border-left: 5px solid #15803D; margin-bottom:10px;">
          <div style="font-weight:900; font-size:1.05rem; color:#0F172A; margin-bottom:4px;">🏨 {hotel_nom_act}</div>
          <div style="font-size:0.88rem; color:#0F172A; margin-bottom:4px;">📍 {hotel_dir_act}</div>
          <div style="font-size:0.78rem; color:#334155;">Coordenadas: {hotel_lat_act:.6f}, {hotel_lon_act:.6f}</div>
        </div>
        """, unsafe_allow_html=True)

        ch_btn1, ch_btn2 = st.columns(2)
        with ch_btn1:
            st.link_button("🗺️ Ver en Maps", gmaps_hotel_search, use_container_width=True)
        with ch_btn2:
            st.link_button("🧭 Cómo llegar", gmaps_hotel_dir, use_container_width=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.expander("✏️ Editar datos del hotel", expanded=False):
            with st.form("form_editar_hotel"):
                h_n = st.text_input("Nombre Hotel:", value=hotel_nom_act)
                h_d = st.text_input("Dirección:", value=hotel_dir_act)
                h_lt = st.number_input("Latitud:", value=float(hotel_lat_act), format="%.6f")
                h_ln = st.number_input("Longitud:", value=float(hotel_lon_act), format="%.6f")
                if st.form_submit_button("💾 Guardar Hotel"):
                    st.session_state.config_viaje["hotel"] = {"nombre": h_n, "direccion": h_d, "lat": h_lt, "lon": h_ln}
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.toast("Hotel base actualizado.", icon="🏨")
                    st.rerun()

    st.markdown("---")
    st.markdown('<div class="ny-card-header">🔄 Sincronización de Listas de Google Maps</div>', unsafe_allow_html=True)
    st.caption("Puedes cambiar el nombre o la URL compartida de cualquier lista aquí mismo. Después pulsa sincronizar para importar los lugares nuevos.")
