function togglePassword() {

    const password = document.getElementById("password");

    const icon = document.getElementById("passwordIcon");


    if (password.type === "password") {

        password.type = "text";

        icon.classList.remove("fa-eye");

        icon.classList.add("fa-eye-slash");

    } else {

        password.type = "password";

        icon.classList.remove("fa-eye-slash");

        icon.classList.add("fa-eye");

    }

}

document.addEventListener("DOMContentLoaded", function () {

    function appliquerModeAutomatique() {

        const maintenant = new Date();

        const heure = maintenant.getHours();

        /*
         * Mode nuit :
         * de 22h00 à 06h59
         */

        const modeNuit = (heure >= 22 || heure < 7);

        document.body.classList.toggle("dark-mode", modeNuit);

    }

    // Appliquer immédiatement
    appliquerModeAutomatique();

    // Vérifier régulièrement
    setInterval(appliquerModeAutomatique, 60000);

});
