# 🗽 NYC Voyage · Winter Edition (26 Dic 2026 - 4 Ene 2027)

Una aplicación web móvil y de escritorio desarrollada con Streamlit y mapas de Google Maps para tu viaje de fin de año en Nueva York.

---

## 🌟 Novedades & Características

1. **⚡ Recálculo Inteligente de Categorías**:
   - Algoritmo de clasificación semántica estricta que distingue con precisión pizzerías, delis, clubs de jazz, cafeterías, outlets, miradores y parques sin falsos positivos.
   - Botón directo **"⚡ Recalcular Categorías"** en la cabecera para re-analizar todos los sitios guardados.
   - Posibilidad de cambiar la categoría de cualquier sitio manualmente desde su ficha.

2. **🎨 Nuevo Diseño Editorial Ultra-Aesthetic**:
   - Paleta neutra limpia de lujo (Obsidian `#0F172A`, Slate, Warm White `#F8F9FA` y detalles suaves).
   - Tipografía editorial elegante (`Playfair Display` + `Plus Jakarta Sans`).
   - Fichas táctiles redondeadas, micro-interacciones suaves y diseño adaptado a smartphone.

3. **🗺️ Mapa Interactivo de Google Maps**:
   - Pines circulares blancos con sombras idénticos a las listas compartidas de Google Maps.
   - Al pulsar cualquier pin, se abre la ficha con dirección real, botón directo para abrir en la app de Google Maps y cálculo de ruta a pie desde el Hotel.
   - Capas: Google Maps Callejero, Satélite Híbrido, Terreno y OpenStreetMap.

4. **🌧️ Modo Lluvia con Clima en Tiempo Real**:
   - Conexión en vivo con la API oficial de **Open-Meteo** para Manhattan.
   - Consulta de temperatura y condiciones actuales en directo.
   - Selector por día (Días 1 a 10) con probabilidad de lluvia (%) y alerta automática de precipitaciones.
   - **Sustitución inteligente 1-clic**: encuentra los sitios a cubierto más cercanos geográficamente a tus planes al aire libre y te permite intercambiarlos al instante.

5. **💵 Calculadora Exclusiva de Divisas & Cuentas NY**:
   - **Cambio de moneda en vivo (USD ↔ EUR)** con tasa de cambio oficial actualizada en tiempo real.
   - **Calculadora oficial de NY**: Sales Tax del 8.875% (con exención para ropa/calzado < $110), cálculo de propinas (15% al 25%) y desglose total en USD y Euros.
   - División de cuenta automática entre comensales.

6. **🔄 Sincronización con Listas de Google Maps**:
   - Sincroniza tus listas compartidas (Tiendas & Outlets, NY Sweets, Food, Rooftop, Spots, etc.) y añade automáticamente lugares nuevos clasificados.

---

## 🚀 Cómo Ejecutar la App

En la consola de comandos de tu ordenador, dentro de la carpeta `NY`:

```bash
python -m streamlit run app.py --server.address 0.0.0.0
```
