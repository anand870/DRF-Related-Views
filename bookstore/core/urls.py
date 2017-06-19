from django.conf.urls import url,include
from core.views import HomeView,BookListView,BookDetailView

urlpatterns = [
    url(r'^$', HomeView.as_view(),name="home"),
    url(r'^books/(?P<pk>[0-9]+)/$',BookDetailView.as_view(),name="book_detail"),
    url(r'^books/$',BookListView.as_view(),name="book_list")
]


