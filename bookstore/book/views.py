from rest_framework.generics import ListAPIView
from relatedviews import mixins
from models import Book,Author
from serializer import BookSerializer

class BookListView(mixins.ListAPIView):
   queryset = Book.objects
   serializer_class = BookSerializer
   template_name = "book/listing.html"
