from operator import itemgetter
from urlparse import urlparse
import datetime
import urllib
from rest_framework import generics
from rest_framework.views import APIView as GAPIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.http.request import QueryDict
from django.core.urlresolvers import resolve,reverse
from collections import OrderedDict
from django.conf import settings
from django.utils.http import is_safe_url
from relatedviews.rvutils import subtractlists
from django.http.response import *

AS_MAIN=1
class Memoized(object):
    excluded_renderer = ('api','json')

    def __init__(self, func):
        self._func = func
        self._cache = {}

    def _create_cache_key(self,args,kwargs,initkwargs):
        kwargs.update(initkwargs)
        hashable_kwargs = filter(lambda x,H=H: isinstance(x[1],H),kwargs.items())
        return hash(tuple(sorted(hashable_kwargs+[self._func.__name__])))
    
    def _get_set_cache(self,args,kwargs,cache_key):
        value = self._func(*args,**kwargs)
        cache_duration = getattr(self._func._class,'cache_duration',settings.CACHE_DURATION)
        cache.set(cache_key,value,cache_duration)
        return value

    def _memoize_renderer(self,request):
        return request.accepted_renderer.format not in self.excluded_renderer

    def __call__(self, *args, **kwargs):
        cache_key = self._create_cache_key(args,kwargs,self._func._initkwargs)
        cache_data = self._memoize_renderer(args[0]) and cache.get(cache_key)
        return cache_data or self._get_set_cache(args,kwargs,cache_key)

class RelatedView(object):
    '''View class makes a view callable from other view. '''
    relview = None
    jointrel = None
    @classmethod
    def as_data(cls,**initkwargs):
        def view(request,*args,**kwargs):
            self=cls(**initkwargs)
            self.retType = 'data'
            self.request = request
            self.format_kwarg = None
            self.args = args
            self.kwargs = kwargs
            resp =  self.get(request,*args,**kwargs)
            if isinstance(resp,Response):resp = resp.data
            return resp

        setattr(view,'__name__',cls.__name__)
        setattr(view,'_class',cls)
        setattr(view,'_initkwargs',initkwargs)
        disablecache = getattr(settings,'MEMO_CACHE_DISABLED',False)
        if not disablecache and initkwargs.get('memoization',getattr(cls,'memoization',False)):
            view = Memoized(view)
        return view


    #def set_related_params(self,params,request,responsedata):
    def set_related_params(self,request,responsedata):
        """ 
        set parameter of related views. Will be available in
        related views kwargs as well as in request.query_params
        of request object passed to the related view
        """
        pass

    def set_pipelined_response(self,view_name,request,responsedata):
        """
        to communicate between different related views use this.
        Responsedata gets cascaded with responses of related views         called in related_views in views.py.
        """
        pass

    def get_final_response(self,request,response):
        """
        it gets the final response after related views have been executed and final response has been appended.
        """
        return response

    def updatekwargs(self,request):
        """
        to update kwargs with query params with greater priority of kwargs.
        """
        updated_dict={}
        if isinstance(request.query_params,QueryDict):
            updated_dict = {k:','.join(v) for k,v in request.query_params.iterlists()}
        else:
            updated_dict = request.query_params
        updated_dict.update(self.kwargs)

        self.kwargs = updated_dict


    def fetch_related(self,request,response,*args,**kwargs):
        ''' fetches data of related views and append to the result '''
        relateddata = {}

        if not isinstance(response.data,dict):
            response = self.get_final_response(request,response)
            return response
        # Retrieve the format of the response
        retformat=request.accepted_renderer.format


        #if hasattr(self,'retType') and self.retType=='data':
            #return response.data
        if not hasattr(self,'related_views') or len(self.related_views)==0:
            response = self.get_final_response(request,response)
            return response

        reqviews = self.get_requested_views(request,retformat)

        if reqviews:
            #check if there is any related view
            if isinstance(self.related_views,dict):
                """
                    A dummy request object is created here which has necessary attributes
                    of original request.The idea is if we pass the original request,then its query_params
                    attribute may have some keys which is common in related views but we dont want to
                    pass it to related view( most common page). The arguments to the related view is 
                    controlled by explicitly passing the name of view separated by colon(:) and the parameter
                    to be passed. e.g self.filter_params['topics:page']=request.query_params.get('page',None)
                """
                #import pdb; pdb.set_trace()
                dummyreq = DummyRequest(request)
                self.updatekwargs(request)
                self.set_related_params(request,response.data)
                #self.set_related_params(updated_dict,request,response.data)
                for name in reqviews:
                    self.set_pipelined_response(name,request,response.data)
                    relobj = self.related_views.get(name,None)
                    dummyreq.query_params={}
                    if relobj:
                        #check that a name and handler function has been provided
                        if len(relobj)<1:
                            raise Exception('Related View must have a handler function')

                        callback = relobj[0]
                        #set the filters for this view which is passed in query_params attribute of request i.e dummyreq
                        if isinstance(relobj[1],str):
                            dummyreq.query_params = self.get_related_params(relobj[1],name)
                        resp = callback(dummyreq,**dummyreq.query_params)
                        if resp is None:
                            raise Exception('The response must be of type Response,dict,list. None received')
                        if type(resp) == Response:
                            resp = resp.data
                        if len(relobj)>2 and relobj[2]==1:
                            response.data[name]=resp
                        elif len(relobj)>1 and not isinstance(relobj[1],str) and relobj[1]==1:
                            response.data[name]=resp
                        else:
                            relateddata[name]=resp
                response.data['extdata']=relateddata
        response = self.get_final_response(request,response)
        if not isinstance(response,(Response,HttpResponse)):
            raise Exception("Expected a django `Response` type to be returned from %s" %self.get_final_response.__name__)
        if hasattr(self,'retType') and self.retType=='data':
            return response.data
        return response

    def get_related_params(self,param_str,viewname):
        related_params = {}
        param_str = param_str.strip(',')
        parameters  = param_str.split(',')
        for p in parameters:
            p = p.strip()
            if p == '*':
                related_params.update(self.kwargs)
            elif '=' in p:
                p_split = p.split('=')
                related_params[p_split[0]]=p_split[1]
            elif ' as ' in p:
                p_split = p.split(' as ')
                if self.kwargs.get(p_split[0]):
                    related_params[p_split[1]]=self.kwargs.get(p_split[0])
            else:
                if self.kwargs.get(p):
                    related_params[p]=self.kwargs.get(p)
        return related_params

    def get_requested_views(self,request,returnformat):
        """get requested views from request.query_params.relview"""
        relview_key = getattr(self,'relview_key','relview')
        reqviews = request.query_params.get(relview_key)
        if reqviews is None:
            # if no relview is passed in query_params then fetch
            # from its attribute relview which is set in urls.py
            if self.relview is not None:
                reqviews = self.relview
        # if related views are not fetched either through query_params
        # or in urls.py and is not jsonrequest then fetch all views
        if reqviews is None: #and returnformat != 'json':
            reqviews = 'all'
        if self.jointrel is not None:
            reqviews = reqviews+','+self.jointrel
        #import pdb; pdb.set_trace()
        if reqviews:
            reqviews = reqviews.split(',')
            relviews = self.related_views.keys()
            include = []
            exclude = []
            for reqview in reqviews:
                if reqview == 'all':
                    include += relviews
                elif reqview[0] == '-':
                    exclude.append(reqview[1:])
                elif reqview not in include:
                    include.append(reqview)
            reqviews = subtractlists(include,exclude)
        return reqviews


class ListAPIView(generics.ListAPIView,RelatedView):

    def list(self,request,*args,**kwargs):
        """ 
        Overridden generics.ListAPIView list method to provide additional 
        functionality of related views data fetching and applied filters addition
        """
        response=super(ListAPIView,self).list(request,*args,**kwargs)
        #add applied_filters to the response which is set when filter_queryset method is called
        response=self.addAppliedFilters(response)
        #fetch data from the related views
        return self.fetch_related(request,response,*args,**kwargs)

    def addAppliedFilters(self,response):
        """
        Add the filters applied to the view to response using the view applied_filters attribute accessible with filters key

        """
        if hasattr(self,'applied_filters') and self.applied_filters:
            if not isinstance(response.data,(list,tuple)):
                response.data['filters']=self.applied_filters
        return response

    def filter_queryset(self,queryset):
	""" 
        Overridden generics.ListAPIView filter_queryset method for adding the filters applied to this view.
        Appends filters applied to ListAPIView instance as applied_filters attribute.
        It fetches the filter from filter_backends by calling its get_applied_filters method.
        """
        filters = {}
        for backend in list(self.filter_backends):
            backendobj = backend()
            queryset = backendobj.filter_queryset(self.request, queryset, self)
            if hasattr(backendobj,'get_applied_filters'):
                filters.update(backendobj.get_applied_filters())
        self. applied_filters = OrderedDict()
        for key,value in filters.items():
            if isinstance(value,datetime.datetime):
                self.applied_filters[key]=value
                del filters[key]
        self.applied_filters.update(sorted(filters.items(),key=itemgetter(1),reverse=True))
        return queryset


class RetrieveAPIView(generics.RetrieveAPIView,RelatedView):

    def retrieve(self,request,*args,**kwargs):
        """ 
        Overridden generics.RetrieveAPIView retrieve method to provide additional 
        functionality of related views data fetching
        """
        response=super(RetrieveAPIView,self).retrieve(request,*args,**kwargs)
        return self.fetch_related(request,response,*args,**kwargs)



class APIView(GAPIView,RelatedView):
    """
        Basic View which inherited from APIView which supports only related data fetching and response format support.

    """
    template_name = None
    def get(self,request,*args,**kwargs):
        response = Response({})
        return self.fetch_related(request,response,*args,**kwargs)

class TabAPIView(RelatedView):
    defaulttab = None
    def fetch_related(self,request,response,*args,**kwargs):
        response = super(TabAPIView,self).fetch_related(request,response,*args,**kwargs)
        if getattr(response,'data',None) and getattr(self,'_currenttab',None):
            response.data['current_tab'] = self._currenttab
        return response

    def get_requested_views(self,request,returnformat):
        """get requested views from request.query_params.relview"""
        if isinstance(request,Request):
            relview_key = getattr(self,'relview_key','relview')
            reqviews = request.query_params.get(relview_key)
            if reqviews is None:
                # if no relview is passed in query_params then fetch
                # from its attribute relview which is set in urls.py
                if self.relview is not None:
                    reqviews = self.relview
            # if related views are not fetched either through query_params
            # or in urls.py and is not jsonrequest then fetch all views
            if reqviews is None: #and returnformat != 'json':
                tabmap = getattr(self,'tabmap',None)
                tabkey = getattr(self,'tab_key','tab')
                if tabmap:
                    currenttab = request.query_params.get(tabkey)
                    if not currenttab:
                        if self.defaulttab is not None:
                            currenttab = self.defaulttab

                    requestedtab = tabmap.get(currenttab,self.defaulttab)
                    if currenttab and requestedtab:
                        reqviews = map(lambda x: x.strip(),requestedtab.strip(',').split(','))
                        self._currenttab = currenttab
            if reqviews:
                return reqviews
        return super(TabAPIView,self).get_requested_views(request,returnformat)
                    
                


class DummyRequest(object):
    """  
        A substitute for rest_framework request object which provides mutable query_params attribute. 
        All the related views are passed DummyRequest instance.The request data that is passed to Related Views are inserted into ites query_params attribute.
    """
    def __init__(self,request):
        self._request=request
        self.query_params = {}
        self.isDummy = True
        self.accepted_renderer = request.accepted_renderer
    
    @property
    def user(self):
        return self._request.user

    def build_absolute_uri(self,location=None):
        return self._request.build_absolute_uri(location)


