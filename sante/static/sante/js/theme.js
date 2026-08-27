document.addEventListener("DOMContentLoaded", function () {

    function appliquerTheme() {

        const heure = new Date().getHours();

        const modeNuit = heure >= 20 || heure < 7;

        if (modeNuit) {
            document.documentElement.classList.add("dark-mode");
        } else {
            document.documentElement.classList.remove("dark-mode");
        }
    }

    // Appliquer immédiatement
    appliquerTheme();

    // Vérifier automatiquement toutes les minutes
    setInterval(appliquerTheme, 60000);

});