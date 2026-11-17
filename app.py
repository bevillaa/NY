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


# ─────────────────────────────────────────────────────────────────────────────
# NUEVA PESTAÑA: LISTAS DE GOOGLE MAPS
# Se conserva íntegro el código de gestión y sincronización existente.
# ─────────────────────────────────────────────────────────────────────────────
if seccion_principal == "🗒️Listas":
    st.markdown("---")
    st.markdown('<div class="ny-card-header">🔄 Sincronización de Listas de Google Maps</div>', unsafe_allow_html=True)
    st.caption("Se puede cambiar el nombre o la URL de cualquier lista, después pulsar sincronizar para importar los lugares nuevos.")

    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])
    if not listas_config:
        st.info("Todavía no hay listas de Google Maps guardadas.")
    else:
        if st.button("🔄 Sincronizar todas las listas", key="btn_sync_all_gmaps", use_container_width=True, type="primary"):
            ejecutar_sincronizacion_listas_gmaps()

    for idx_lst, lst_data in enumerate(listas_config):
        nombre_lista = str(lst_data.get("nombre", f"Lista {idx_lst + 1}"))
        url_lista = str(lst_data.get("url", ""))
        sufijo_edicion = hashlib.sha1(f"{nombre_lista}\0{url_lista}".encode("utf-8")).hexdigest()[:10]
        key_ed_nombre = f"gmaps_edit_nombre_{idx_lst}_{sufijo_edicion}"
        key_ed_url = f"gmaps_edit_url_{idx_lst}_{sufijo_edicion}"

        with st.container(key=f"saved-heading-row-list-{idx_lst}"):
            col_nombre, col_edit = st.columns([9.45, 0.55], gap="small", vertical_alignment="center")
            with col_nombre:
                st.markdown(
                    f"<div style='font-weight:800; color:#0F172A; overflow-wrap:anywhere;'>{idx_lst + 1}. {html.escape(nombre_lista)}</div>"
                    f"<div class='gmaps-list-url' style='font-size:0.76rem; color:#475569; margin-top:2px; margin-bottom:6px;'>{html.escape(url_lista)}</div>",
                    unsafe_allow_html=True
                )
            with col_edit:
                with st.container(key=f"saved-edit-button-wrap-list-{idx_lst}"):
                    if st.button(" ", key=f"btn_ed_pool_list_{idx_lst}", help="Editar lista"):
                        actual = st.session_state.get("lista_gmaps_editando")
                        st.session_state.lista_gmaps_editando = None if actual == idx_lst else idx_lst
                        for clave in (key_ed_nombre, key_ed_url):
                            st.session_state.pop(clave, None)
                        st.rerun()

        if st.session_state.get("lista_gmaps_editando") == idx_lst:
            st.markdown(f"**Editar lista: {html.escape(nombre_lista)}**")
            with st.form(f"form_editar_lista_gmaps_{idx_lst}"):
                nuevo_nombre_lista = st.text_input("Nombre de la lista:", value=nombre_lista, key=key_ed_nombre)
                nueva_url_lista = st.text_input("URL compartida de Google Maps:", value=url_lista,
                    placeholder="https://maps.app.goo.gl/...", key=key_ed_url)
                guardar_lista = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
                cancelar_lista = st.form_submit_button("Cancelar", use_container_width=True)
                if guardar_lista:
                    nombre_limpio = nuevo_nombre_lista.strip()
                    url_limpia = nueva_url_lista.strip()
                    partes_url = urllib.parse.urlparse(url_limpia)
                    if not nombre_limpio:
                        st.error("El nombre de la lista no puede estar vacío.")
                    elif partes_url.scheme not in ("http", "https") or not partes_url.netloc:
                        st.error("Introduce una URL completa que empiece por https:// o http://.")
                    else:
                        listas_actualizadas = list(st.session_state.config_viaje.get("listas_gmaps", []))
                        if idx_lst < len(listas_actualizadas):
                            listas_actualizadas[idx_lst] = {"nombre": nombre_limpio, "url": url_limpia}
                            st.session_state.config_viaje["listas_gmaps"] = listas_actualizadas
                            if guardar_config_viaje(st.session_state.config_viaje):
                                st.session_state.lista_gmaps_editando = None
                                st.toast("Lista de Google Maps actualizada.", icon="✅")
                                st.rerun()
                elif cancelar_lista:
                    st.session_state.lista_gmaps_editando = None
                    st.rerun()

    with st.expander("➕ Añadir nueva lista de Google Maps"):
        with st.form("form_nueva_lista_gmaps"):
            n_nombre_l = st.text_input("Nombre de la lista (ej: Rooftops & Bares):")
            n_url_l = st.text_input("URL compartida de Google Maps (maps.app.goo.gl/...):")
            if st.form_submit_button("Añadir Lista"):
                url_nueva = (n_url_l or "").strip()
                partes_url = urllib.parse.urlparse(url_nueva)
                if not n_nombre_l.strip():
                    st.error("Introduce un nombre para la lista.")
                elif partes_url.scheme not in ("http", "https") or not partes_url.netloc:
                    st.error("Introduce una URL completa que empiece por https:// o http://.")
                else:
                    listas_actualizadas = list(st.session_state.config_viaje.get("listas_gmaps", []))
                    listas_actualizadas.append({"nombre": n_nombre_l.strip(), "url": url_nueva})
                    st.session_state.config_viaje["listas_gmaps"] = listas_actualizadas
                    if guardar_config_viaje(st.session_state.config_viaje):
                        st.success("Lista guardada.")
                        st.rerun()
