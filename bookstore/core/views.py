from relatedviews import mixins

from book.views import BookListView
class HomeView(mixins.APIView):
    template_name = "core/home.html"
    related_views = {
        'books':(BookListView.as_data(),mixins.AS_MAIN)
        
    }
