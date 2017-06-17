from django.conf.urls import url,include

urlpatterns = [
    url(r'^books/', BookListView.as_view(),name="booklist"),
]

