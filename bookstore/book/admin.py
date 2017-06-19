from django.contrib import admin
from models import Book,Publication,Genere

class BookAdmin(admin.ModelAdmin):
    pass

class GenereAdmin(admin.ModelAdmin):
    pass

class PublicationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Book,BookAdmin)
admin.site.register(Genere,GenereAdmin)
admin.site.register(Publication,PublicationAdmin)
