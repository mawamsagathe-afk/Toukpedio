document.addEventListener("DOMContentLoaded", function () {

    const cards = document.querySelectorAll(".child-card");

    /*
    ==========================================
    ANIMATION AU SURVOL
    ==========================================
    */

    cards.forEach(function (card) {

        card.addEventListener("mouseenter", function () {

            card.style.zIndex = "5";

        });

        card.addEventListener("mouseleave", function () {

            card.style.zIndex = "1";

        });

    });


    /*
    ==========================================
    ANIMATION DES BOUTONS
    ==========================================
    */

    const buttons =
        document.querySelectorAll(".action-btn");

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            button.classList.add("clicked");

            setTimeout(function () {

                button.classList.remove("clicked");

            }, 250);

        });

    });


    /*
    ==========================================
    APPARITION PROGRESSIVE
    ==========================================
    */

    const observer =
        new IntersectionObserver(
            function (entries) {

                entries.forEach(function (entry) {

                    if (entry.isIntersecting) {

                        entry.target.classList.add(
                            "visible"
                        );

                    }

                });

            },
            {
                threshold: 0.1
            }
        );


    cards.forEach(function (card) {

        observer.observe(card);

    });

});