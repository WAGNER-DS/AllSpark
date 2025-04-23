window.addEventListener("resize", () => {
    // Tenta acessar o iframe
    const iframe = document.querySelector("iframe");

    if (iframe && iframe.contentWindow) {
        try {
            // Tenta acessar o objeto Leaflet dentro do iframe e forçar um evento de resize
            iframe.contentWindow.dispatchEvent(new Event("resize"));
        } catch (e) {
            console.warn("Não foi possível acessar contentWindow do iframe (provavelmente bloqueado por sandbox).", e);
        }
    }
});
