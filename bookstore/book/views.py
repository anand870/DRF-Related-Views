import django_filters
from rest_framework import serializers
from relatedviews import mixins,filters
from relatedviews.filters import MutableDjangoFilterBackend
from models import Book,Author

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class BookFilterClass(django_filters.FilterSet):
     rating = filters.ListFilter(name="rating",lookup_expr="in")
     class Meta:
        model = Book
        fields = ('rating',)

class BookList(mixins.ListAPIView):
   queryset = Book.objects
   serializer_class = BookSerializer
   filter_class =  BookFilterClass
   filter_backends = (MutableDjangoFilterBackend,)

class BookDetail(mixins.RetrieveAPIView):
    queryset = Book.objects
    serializer_class = BookSerializer
    template_name = "book/detail.html"
