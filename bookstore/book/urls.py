from django.conf.urls import url,include
from views import BookListView

urlpatterns = [
    url(r'', BookListView.as_view(),name="booklist"),
]

