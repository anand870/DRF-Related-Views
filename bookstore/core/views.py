from relatedviews import mixins
from book.views import BookList

class BookListView(mixins.APIView):
    template_name = "book/listing.html"
    related_views = {
       'books':(BookList.as_data(),'*',mixins.AS_MAIN), 
       #'featured_books':(BookList.as_data,'featured=1',mixins.AS_MAIN),
    }

class BookDetailView(mixins.APIView):
    template_name = "book/detail.html"

class HomeView(mixins.APIView):
    template_name = "core/home.html"
    related_views = {
        'books':(BookList.as_data(),mixins.AS_MAIN)
        
    }

