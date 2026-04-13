// Configuración
const RAWG_API_KEY = '0c2a9ea573034836b3c0de9916085843';

async function obtenerFichaJuego(nombreBusqueda) {
    const contenedor = document.getElementById("game-description-text");
    const btn = document.getElementById("read-more-btn");

    try {
        // 1. Limpiamos el nombre para mejorar la búsqueda
        const nombreLimpio = nombreBusqueda.split(':')[0].split('-')[0].trim();
        console.log("Buscando en APIs para:", nombreLimpio);

        // 2. Buscar en RAWG (Búsqueda general para obtener el ID)
        const resBusqueda = await fetch(`https://api.rawg.io/api/games?key=${RAWG_API_KEY}&search=${encodeURIComponent(nombreLimpio)}`);
        const datosBusqueda = await resBusqueda.json();

        if (!datosBusqueda.results || datosBusqueda.results.length === 0) {
            if (contenedor) contenedor.innerText = "No se encontró información en la base de datos de RAWG.";
            return;
        }

        // 3. Obtener el detalle completo usando el ID
        const juegoId = datosBusqueda.results[0].id;
        const resDetalle = await fetch(`https://api.rawg.io/api/games/${juegoId}?key=${RAWG_API_KEY}`);
        const detalle = await resDetalle.json();

        // 4. Extraer la descripción
        const descripcionFinal = detalle.description || detalle.description_raw || "Descripción no disponible para este título.";

        // 5. Inyectar en el HTML
        if (contenedor) {
            contenedor.innerHTML = descripcionFinal;

            // 6. Lógica del botón "Mostrar más"
            // Esperamos un momento a que el navegador renderice para medir la altura
            setTimeout(() => {
                // Si la altura del contenido es mayor que la del contenedor (limitado a 3 líneas)
                // Usamos 100px como umbral aproximado para 3 líneas de texto
                if (contenedor.scrollHeight > 80) {
                    if (btn) btn.style.display = "block";
                } else {
                    if (btn) btn.style.display = "none";
                }
            }, 100);

            console.log("¡Descripción cargada con éxito!");
        }

    } catch (error) {
        console.error("Error en la carga:", error);
        if (contenedor) contenedor.innerText = "Error al conectar con la base de datos de información.";
    }
}