// Configuración
const RAWG_API_KEY = '0c2a9ea573034836b3c0de9916085843';

async function obtenerFichaJuego(nombreBusqueda) {
    const contenedor = document.getElementById("game-description-text");
    const btn = document.getElementById("read-more-btn");

    try {
        const nombreLimpio = nombreBusqueda.split(':')[0].split('-')[0].trim();
        console.log("Buscando en APIs para:", nombreLimpio);

        const resBusqueda = await fetch(`https://api.rawg.io/api/games?key=${RAWG_API_KEY}&search=${encodeURIComponent(nombreLimpio)}`);
        const datosBusqueda = await resBusqueda.json();

        if (!datosBusqueda.results || datosBusqueda.results.length === 0) {
            if (contenedor) contenedor.innerText = "No information found in the RAWG database.";
            return;
        }

        const juegoId = datosBusqueda.results[0].id;
        const resDetalle = await fetch(`https://api.rawg.io/api/games/${juegoId}?key=${RAWG_API_KEY}`);
        const detalle = await resDetalle.json();

        const descripcionFinal = detalle.description || detalle.description_raw || "Description not available for this title.";

        if (contenedor) {
            contenedor.innerHTML = descripcionFinal;

            setTimeout(() => {
                if (contenedor.scrollHeight > 80) {
                    if (btn) btn.style.display = "block";
                } else {
                    if (btn) btn.style.display = "none";
                }
            }, 100);

            console.log("Description loaded successfully.");
        }

    } catch (error) {
        console.error("Error en la carga:", error);
        if (contenedor) contenedor.innerText = "Error connecting to the information database.";
    }
}
