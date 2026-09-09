from django.urls import path
from . import views


app_name = "sante"


urlpatterns = [

    # =========================================================
    # ACCUEIL
    # =========================================================

    path(
        "",
        views.accueil,
        name="accueil"
    ),


    # =========================================================
    # CONNEXION
    # =========================================================

    path(
        "connexion/",
        views.connexion,
        name="connexion"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    path(
        "inscription/",
        views.inscription,
        name="inscription"
    ),


    # =========================================================
    # TABLEAU DE BORD PARENT
    # =========================================================

    path(
        "tableau_bord_parent/",
        views.tableau_bord_parent,
        name="tableau_bord_parent"
    ),

    path(
        "assistant-gemini/",
        views.assistant_gemini,
        name="assistant_gemini"
    ),


    # =========================================================
    # ADMINISTRATION
    # =========================================================

    path(
        "connexion-admin/",
        views.connexion_admin,
        name="connexion_admin"
    ),

    path(
        "tableau-de-bord/admin/",
        views.tableau_bord_admin,
        name="tableau_bord_admin"
    ),

    path(
        "administration/",
        views.administration,
        name="administration"
    ),

    path(
        "administration/enfants/",
        views.administration_enfants,
        name="admin_enfants"
    ),


    # =========================================================
    # ADMIN — ENFANTS
    # =========================================================

    path(
        "administration/enfant/ajouter/",
        views.administration_ajouter_enfant,
        name="administration_ajouter_enfant"
    ),

    path(
        "administration/enfant/<int:enfant_id>/",
        views.administration_enfant_detail,
        name="administration_enfant_detail"
    ),
    
    path(
    "administration/enfant/<int:enfant_id>/partage/ajouter/",
    views.administration_ajouter_partage,
    name="administration_ajouter_partage"
),

    path(
        "administration/enfant/<int:enfant_id>/modifier/",
        views.administration_modifier_enfant,
        name="administration_modifier_enfant"
    ),

    path(
        "administration/enfant/<int:enfant_id>/supprimer/",
        views.administration_supprimer_enfant,
        name="administration_supprimer_enfant"
    ),


    # =========================================================
    # ADMIN — CONSULTATIONS
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/consultation/ajouter/",
        views.administration_ajouter_consultation,
        name="administration_ajouter_consultation"
    ),

    path(
        "administration/consultation/<int:consultation_id>/modifier/",
        views.administration_modifier_consultation,
        name="administration_modifier_consultation"
    ),

    path(
        "administration/consultation/<int:consultation_id>/supprimer/",
        views.administration_supprimer_consultation,
        name="administration_supprimer_consultation"
    ),


    # =========================================================
    # ADMIN — VACCINATIONS
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/vaccination/ajouter/",
        views.administration_ajouter_vaccination,
        name="administration_ajouter_vaccination"
    ),

    path(
        "administration/vaccination/<int:vaccination_id>/modifier/",
        views.administration_modifier_vaccination,
        name="administration_modifier_vaccination"
    ),

    path(
        "administration/vaccination/<int:vaccination_id>/supprimer/",
        views.administration_supprimer_vaccination,
        name="administration_supprimer_vaccination"
    ),


    # =========================================================
    # ADMIN — SYMPTÔMES
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/symptome/ajouter/",
        views.administration_ajouter_symptome,
        name="administration_ajouter_symptome"
    ),

    path(
        "administration/symptome/<int:symptome_id>/modifier/",
        views.administration_modifier_symptome,
        name="administration_modifier_symptome"
    ),

    path(
        "administration/symptome/<int:symptome_id>/supprimer/",
        views.administration_supprimer_symptome,
        name="administration_supprimer_symptome"
    ),


    # =========================================================
    # ADMIN — TEMPÉRATURES
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/temperature/ajouter/",
        views.administration_ajouter_temperature,
        name="administration_ajouter_temperature"
    ),

    path(
        "administration/temperature/<int:temperature_id>/modifier/",
        views.administration_modifier_temperature,
        name="administration_modifier_temperature"
    ),

    path(
        "administration/temperature/<int:temperature_id>/supprimer/",
        views.administration_supprimer_temperature,
        name="administration_supprimer_temperature"
    ),


    # =========================================================
    # ADMIN — CROISSANCE
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/croissance/ajouter/",
        views.administration_ajouter_croissance,
        name="administration_ajouter_croissance"
    ),

    path(
        "administration/croissance/<int:croissance_id>/modifier/",
        views.administration_modifier_croissance,
        name="administration_modifier_croissance"
    ),

    path(
        "administration/croissance/<int:croissance_id>/supprimer/",
        views.administration_supprimer_croissance,
        name="administration_supprimer_croissance"
    ),


    # =========================================================
    # ADMIN — BIEN-ÊTRE
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/bien-etre/ajouter/",
        views.administration_ajouter_bien_etre,
        name="administration_ajouter_bien_etre"
    ),

    path(
        "administration/bien-etre/<int:bien_etre_id>/modifier/",
        views.administration_modifier_bien_etre,
        name="administration_modifier_bien_etre"
    ),

    path(
        "administration/bien-etre/<int:bien_etre_id>/supprimer/",
        views.administration_supprimer_bien_etre,
        name="administration_supprimer_bien_etre"
    ),


    # =========================================================
    # ADMIN — RENDEZ-VOUS
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/rendez-vous/ajouter/",
        views.administration_ajouter_rendez_vous,
        name="administration_ajouter_rendez_vous"
    ),

    path(
        "administration/rendez-vous/<int:rendez_vous_id>/modifier/",
        views.administration_modifier_rendez_vous,
        name="administration_modifier_rendez_vous"
    ),

    path(
        "administration/rendez-vous/<int:rendez_vous_id>/supprimer/",
        views.administration_supprimer_rendez_vous,
        name="administration_supprimer_rendez_vous"
    ),


    # =========================================================
    # ADMIN — TRAITEMENTS
    # =========================================================

    path(
        "administration/enfant/<int:enfant_id>/traitement/ajouter/",
        views.administration_ajouter_traitement,
        name="administration_ajouter_traitement"
    ),

    path(
        "administration/traitement/<int:traitement_id>/modifier/",
        views.administration_modifier_traitement,
        name="administration_modifier_traitement"
    ),

    path(
        "administration/traitement/<int:traitement_id>/supprimer/",
        views.administration_supprimer_traitement,
        name="administration_supprimer_traitement"
    ),


    # =========================================================
    # ADMIN — PARTAGE ENTRE PARENTS
    # =========================================================

    path(
        "administration/partage/<int:partage_id>/modifier/",
        views.administration_modifier_partage,
        name="administration_modifier_partage"
    ),

    path(
        "administration/partage/<int:partage_id>/supprimer/",
        views.administration_supprimer_partage,
        name="administration_supprimer_partage"
    ),


    # =========================================================
    # ADMIN — MODE GARDE
    # =========================================================
    
    path(
    "administration/enfant/<int:enfant_id>/mode-garde/ajouter/",
    views.administration_ajouter_mode_garde,
    name="administration_ajouter_mode_garde"
    ),

    path(
        "administration/mode-garde/<int:mode_garde_id>/modifier/",
        views.administration_modifier_mode_garde,
        name="administration_modifier_mode_garde"
    ),

    path(
        "administration/mode-garde/<int:mode_garde_id>/supprimer/",
        views.administration_supprimer_mode_garde,
        name="administration_supprimer_mode_garde"
    ),

    path(
        "administration/mode-garde/<int:mode_garde_id>/desactiver/",
        views.administration_desactiver_mode_garde,
        name="administration_desactiver_mode_garde"
    ),


    # =========================================================
    # ENFANTS — ESPACE PARENT
    # =========================================================

    path(
        "enfants/",
        views.enfant,
        name="enfant"
    ),

    path(
        "enfants/ajouter/",
        views.ajouter_enfant,
        name="ajouter_enfant"
    ),

    # IMPORTANT :
    # la vue modifier_enfant attend enfant_id
    path(
        "enfants/<int:enfant_id>/modifier/",
        views.modifier_enfant,
        name="modifier_enfant"
    ),

    path(
        "enfant/<int:enfant_id>/",
        views.detail_enfant,
        name="detail_enfant"
    ),


    # =========================================================
    # SYMPTÔMES — ESPACE PARENT
    # =========================================================

    path(
        "enfant/<int:enfant_id>/symptome/ajouter/",
        views.ajouter_symptome,
        name="ajouter_symptome"
    ),

    path(
        "symptome/<int:symptome_id>/modifier/",
        views.modifier_symptome,
        name="modifier_symptome"
    ),

    path(
        "symptome/<int:symptome_id>/supprimer/",
        views.supprimer_symptome,
        name="supprimer_symptome"
    ),


    # =========================================================
    # CROISSANCE
    # =========================================================

    path(
        "enfants/<int:enfant_id>/croissance/",
        views.croissance,
        name="croissance"
    ),


    # =========================================================
    # CONSULTATIONS
    # =========================================================

     path(
            "enfants/<int:enfant_id>/consultations/",
            views.liste_consultations,
            name="consultations"
        ),

    path(
        "enfants/<int:enfant_id>/consultations/ajouter/",
        views.ajouter_consultation,
        name="ajouter_consultation"
    ),


    # =========================================================
    # VACCINATIONS
    # =========================================================

    path(
        "enfants/<int:enfant_id>/vaccinations/",
        views.vaccination,
        name="vaccination"
    ),

    path(
        "enfant/<int:enfant_id>/vaccination/ajouter/",
        views.ajouter_vaccination,
        name="ajouter_vaccination"
    ),


    # =========================================================
    # RENDEZ-VOUS
    # =========================================================

    path(
        "enfants/<int:enfant_id>/rendez-vous/",
        views.rendez_vous,
        name="rendez_vous"
    ),


    # =========================================================
    # BIEN-ÊTRE
    # =========================================================

    path(
        "enfants/<int:enfant_id>/bien-etre/",
        views.bien_etre,
        name="bien_etre"
    ),


    # =========================================================
    # TEMPÉRATURE
    # =========================================================

    path(
        "enfant/<int:enfant_id>/temperature/",
        views.suivi_temperature,
        name="suivi_temperature"
    ),

    path(
        "temperature/<int:temperature_id>/supprimer/",
        views.supprimer_temperature,
        name="supprimer_temperature"
    ),


    # =========================================================
    # TRAITEMENTS
    # =========================================================

    path(
        "enfants/<int:enfant_id>/traitements/",
        views.traitements,
        name="traitements"
    ),

    path(
        "enfants/<int:enfant_id>/traitements/ajouter/",
        views.ajouter_traitement,
        name="ajouter_traitement"
    ),

    path(
        "traitements/<int:traitement_id>/prise/",
        views.enregistrer_prise,
        name="enregistrer_prise"
    ),


    # =========================================================
    # PARTAGE ENTRE PARENTS
    # =========================================================

    path(
        "enfants/<int:enfant_id>/inviter-parent/",
        views.inviter_parent,
        name="inviter_parent"
    ),

    path(
        "partage/<int:partage_id>/accepter/",
        views.accepter_partage,
        name="accepter_partage"
    ),


    # =========================================================
    # MODE GARDE — ESPACE PARENT
    # =========================================================

    path(
        "enfants/<int:enfant_id>/mode-garde/creer/",
        views.creer_mode_garde,
        name="creer_mode_garde"
    ),

    path(
        "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/",
        views.mode_garde_detail,
        name="mode_garde_detail"
    ),

    path(
        "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/desactiver/",
        views.desactiver_mode_garde,
        name="desactiver_mode_garde"
    ),

    # Accès public par token
    path(
        "mode-garde/<uuid:token>/",
        views.consulter_mode_garde,
        name="consulter_mode_garde"
    ),

    path(
        "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/pdf/",
        views.mode_garde_pdf,
        name="mode_garde_pdf"
    ),

    path(
        "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/image/",
        views.mode_garde_image,
        name="mode_garde_image"
    ),

    path(
        "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/whatsapp/",
        views.mode_garde_whatsapp,
        name="mode_garde_whatsapp"
    ),

    path(
        "enfants/<int:enfant_id>/mode-garde/<int:mode_garde_id>/sms/",
        views.mode_garde_sms,
        name="mode_garde_sms"
    ),
]