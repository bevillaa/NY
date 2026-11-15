                    fr_url = f"https://www.flightradar24.com/data/flights/{cod.lower()}"
                    st.link_button(f"✈️ {cod}", fa_url, use_container_width=True)
                    st.markdown(f"<div style='text-align:center; font-size:0.76rem;'><a href='{fr_url}' target='_blank' style='color:#1D4ED8; font-weight:700;'>Flightradar24 ↗</a></div>", unsafe_allow_html=True)

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
    st.caption("Pulsa sincronizar para importar nuevos lugares.")

    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])

    for idx_lst, lst_data in enumerate(listas_config):
        col_l1, col_l2 = st.columns([3.5, 1.5])
        with col_l1:
            st.markdown(f"**{idx_lst+1}. {lst_data['nombre']}**  \n`{lst_data['url']}`")
        with col_l2:
            if st.button("🔄 Sincronizar", key=f"btn_sync_list_{idx_lst}", use_container_width=True):
                with st.spinner(f"Descargando de {lst_data['nombre']}..."):
                    descargados = extraer_lugares_lista_gmaps(lst_data["url"], lst_data["nombre"])
                    if descargados:
                        existentes = set(x.get("nombre", "").lower() for x in st.session_state.lugares)
                        agregados = 0
                        max_id_act = max([x.get("id", 0) for x in st.session_state.lugares], default=0)
                        for d_item in descargados:
                            if d_item["nombre"].lower() not in existentes:
                                max_id_act += 1
                                st.session_state.lugares.append({
                                    "id": max_id_act,
                                    "nombre": d_item["nombre"],
                                    "lat": d_item["lat"],
                                    "lon": d_item["lon"],
                                    "dia": 0,
                                    "hora": "",
                                    "direccion": d_item.get("direccion", ""),
                                    "nota": "",
                                    "categoria": d_item["categoria"],
                                    "tipo": d_item["tipo"],
                                    "visitado": False
                                })
                                agregados += 1
                        guardar_itinerario_disco(st.session_state.lugares)
                        st.success(f"✓ Sincronizado: {agregados} sitios nuevos añadidos a Guardados.")
                        st.rerun()
                    else:
                        st.warning("No se pudieron extraer lugares en este momento.")

    with st.expander("➕ Añadir nueva lista de Google Maps"):
        with st.form("form_nueva_lista_gmaps"):
            n_nombre_l = st.text_input("Nombre de la lista (ej: Rooftops & Bares):")
            n_url_l = st.text_input("URL compartida de Google Maps (maps.app.goo.gl/...):")
            if st.form_submit_button("Añadir Lista"):
                if n_nombre_l and n_url_l:
                    listas_config.append({"nombre": n_nombre_l, "url": n_url_l})
                    st.session_state.config_viaje["listas_gmaps"] = listas_config
                    guardar_config_viaje(st.session_state.config_viaje)
                    st.success("Lista guardada.")
                    st.rerun()
