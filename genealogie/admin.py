from django.contrib import admin
from .models import Genealogie


@admin.register(Genealogie)
class GenealogieAdmin(admin.ModelAdmin):
    list_display = (
        "agneau_link",
        "mere_link",
        "pere_link",
        "fa_pct",
        "risque_txt",
    )
    search_fields = (
        "agneau__boucle_ovin",
        "mere__boucle_ovin",
        "pere__boucle_ovin",
    )
    autocomplete_fields = ("agneau", "mere", "pere")
    list_select_related = ("agneau", "mere", "pere")
    ordering = ("agneau__boucle_ovin",)

    @admin.display(description="Agneau", ordering="agneau__boucle_ovin")
    def agneau_link(self, obj):
        return getattr(obj.agneau, "boucle_ovin", obj.agneau_id)

    @admin.display(description="Mère", ordering="mere__boucle_ovin")
    def mere_link(self, obj):
        return getattr(obj.mere, "boucle_ovin", obj.mere_id)

    @admin.display(description="Père", ordering="pere__boucle_ovin")
    def pere_link(self, obj):
        return getattr(obj.pere, "boucle_ovin", obj.pere_id)

    @admin.display(description="Consanguinité", ordering="fa")
    def fa_pct(self, obj):
        # obj.coefficient_consanguinite renvoie le pourcentage (0..100)
        return f"{obj.coefficient_consanguinite:.2f} %"

    @admin.display(description="Risque")
    def risque_txt(self, obj):
        return obj.risque_consanguinite
