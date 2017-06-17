from django.db import models


class Publication(models.Model):
    name = models.CharField(max_length=100)

class Book(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    publish_year = models.IntegerField()
    rating = models.DecimalField(max_digits=3,decimal_places=2)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    image = models.ImageField(upload_to="images/",null=True,blank=True)
    authors = models.ManyToManyField("Author")
    genere = models.ManyToManyField("Genere")
    publication = models.ForeignKey("Publication",on_delete=models.SET_NULL,null=True)
    def __unicode__(self):
        return self.title

class Author(models.Model):
    name = models.CharField(max_length=50)
    def __unicode__(self):
        return self.name


class Genere(models.Model):
    name = models.CharField(max_length=50)
    def __unicode__(self):
        return self.name
    
