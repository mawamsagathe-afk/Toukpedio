document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       ANIMATION AU SCROLL
    ===================================================== */

    const elements =
        document.querySelectorAll(".reveal");

    const observer =
        new IntersectionObserver(
            function (entries) {

                entries.forEach(function (entry) {

                    if (entry.isIntersecting) {

                        entry.target.classList.add("active");

                        observer.unobserve(
                            entry.target
                        );
                    }

                });

            },
            {
                threshold: 0.15
            }
        );


    elements.forEach(function (element) {

        observer.observe(element);

    });


    /* =====================================================
       COMPTEURS
    ===================================================== */

    const counters =
        document.querySelectorAll(".stat-number");


    const counterObserver =
        new IntersectionObserver(
            function (entries) {

                entries.forEach(function (entry) {

                    if (!entry.isIntersecting) {
                        return;
                    }

                    const counter =
                        entry.target;

                    const original =
                        counter.textContent.trim();

                    const target =
                        parseInt(
                            original.replace(/\D/g, ""),
                            10
                        );

                    let current = 0;

                    const duration = 1200;

                    const step =
                        target / (duration / 16);


                    function animate() {

                        current += step;

                        if (current >= target) {

                            counter.textContent =
                                original.includes("%")
                                    ? target + "%"
                                    : target;

                            return;
                        }

                        counter.textContent =
                            original.includes("%")
                                ? Math.floor(current) + "%"
                                : Math.floor(current);

                        requestAnimationFrame(
                            animate
                        );
                    }

                    animate();

                    counterObserver.unobserve(
                        counter
                    );

                });

            },
            {
                threshold: .7
            }
        );


    counters.forEach(function (counter) {

        counterObserver.observe(counter);

    });


    /* =====================================================
       EFFET SOURIS SUR LES CARTES
    ===================================================== */

    const cards =
        document.querySelectorAll(
            ".service-card"
        );


    cards.forEach(function (card) {

        card.addEventListener(
            "mousemove",
            function (event) {

                const rect =
                    card.getBoundingClientRect();

                const x =
                    event.clientX - rect.left;

                const y =
                    event.clientY - rect.top;

                const rotateX =
                    (y - rect.height / 2) / 30;

                const rotateY =
                    (rect.width / 2 - x) / 30;


                card.style.transform =
                    `translateY(-10px)
                     perspective(800px)
                     rotateX(${rotateX}deg)
                     rotateY(${rotateY}deg)`;
            }
        );


        card.addEventListener(
            "mouseleave",
            function () {

                card.style.transform =
                    "translateY(0)";

            }
        );

    });


    /* =====================================================
       SCROLL FLUIDE
    ===================================================== */

    document.querySelectorAll(
        'a[href^="#"]'
    ).forEach(function (link) {

        link.addEventListener(
            "click",
            function (event) {

                const targetId =
                    this.getAttribute("href");

                const target =
                    document.querySelector(targetId);

                if (target) {

                    event.preventDefault();

                    target.scrollIntoView({
                        behavior: "smooth"
                    });

                }

            }
        );

    });


    /* =====================================================
       RIPPLE DES BOUTONS
    ===================================================== */

    document.addEventListener(
        "click",
        function (event) {

            const button =
                event.target.closest(
                    ".btn-principal, .btn-secondaire"
                );

            if (!button) {
                return;
            }

            const ripple =
                document.createElement("span");

            ripple.className =
                "ripple";


            const rect =
                button.getBoundingClientRect();


            ripple.style.left =
                `${event.clientX - rect.left}px`;

            ripple.style.top =
                `${event.clientY - rect.top}px`;


            button.appendChild(ripple);


            setTimeout(function () {

                ripple.remove();

            }, 600);

        }
    );

});