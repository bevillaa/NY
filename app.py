    listas_config = st.session_state.config_viaje.get("listas_gmaps", [])
    if not listas_config:
        st.info("Todavía no hay listas de Google Maps guardadas.")

    for idx_lst, lst_data in enumerate(listas_config):
        nombre_lista = str(lst_data.get("nombre", f"Lista {idx_lst + 1}"))
        url_lista = str(lst_data.get("url", ""))
        sufijo_edicion = hashlib.sha1(f"{nombre_lista}\0{url_lista}".encode("utf-8")).hexdigest()[:10]
        key_ed_nombre = f"gmaps_edit_nombre_{idx_lst}_{sufijo_edicion}"
        key_ed_url = f"gmaps_edit_url_{idx_lst}_{sufijo_edicion}"

        st.markdown(
            f"<div style='font-weight:800; color:#0F172A; overflow-wrap:anywhere;'>{idx_lst + 1}. {html.escape(nombre_lista)}</div>"
            f"<div class='gmaps-list-url' style='font-size:0.76rem; color:#475569; margin-top:2px; margin-bottom:6px;'>{html.escape(url_lista)}</div>",
            unsafe_allow_html=True
        )
        with st.container(key=f"gmaps-actions-{idx_lst}"):
            col_sync, col_edit = st.columns(2, gap="small")
            with col_sync:
                if st.button("🔄 Sincronizar", key=f"btn_sync_list_{idx_lst}", use_container_width=True):
                    if not url_lista.strip():
                        st.error("Edita la lista e introduce una URL antes de sincronizar.")
                    else:
                        with st.spinner(f"Descargando de {nombre_lista}..."):
                            descargados = extraer_lugares_lista_gmaps(url_lista, nombre_lista)
                            if descargados:
                                existentes = set(x.get("nombre", "").lower() for x in st.session_state.lugares)
                                agregados = 0
                                max_id_act = max([x.get("id", 0) for x in st.session_state.lugares], default=0)
                                for d_item in descargados:
                                    nombre_importado = d_item.get("nombre", "").strip()
                                    if nombre_importado and nombre_importado.lower() not in existentes:
                                        max_id_act += 1
                                        st.session_state.lugares.append({
                                            "id": max_id_act,
                                            "nombre": nombre_importado,
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
                                        existentes.add(nombre_importado.lower())
                                        agregados += 1
                                guardar_itinerario_disco(st.session_state.lugares)
                                st.success(f"✓ Sincronizado: {agregados} sitios nuevos añadidos a Guardados.")
                                st.rerun()
                            else:
                                st.warning("No se pudieron extraer lugares. Comprueba que el enlace sea una lista compartida de Google Maps y que tenga acceso público.")
            with col_edit:
                if st.button("✏️ Editar", key=f"btn_edit_list_{idx_lst}", use_container_width=True):
                    actual = st.session_state.get("lista_gmaps_editando")
                    st.session_state.lista_gmaps_editando = None if actual == idx_lst else idx_lst
                    for clave in (key_ed_nombre, key_ed_url):
                        st.session_state.pop(clave, None)
                    st.rerun()

        if st.session_state.get("lista_gmaps_editando") == idx_lst:
            st.markdown(f"**Editar lista: {html.escape(nombre_lista)}**")
            with st.form(f"form_editar_lista_gmaps_{idx_lst}"):
                nuevo_nombre_lista = st.text_input(
                    "Nombre de la lista:",
                    value=nombre_lista,
                    key=key_ed_nombre
                )
                nueva_url_lista = st.text_input(
                    "URL compartida de Google Maps:",
                    value=url_lista,
                    placeholder="https://maps.app.goo.gl/...",
                    key=key_ed_url
                )
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
