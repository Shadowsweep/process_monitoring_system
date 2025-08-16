from django.urls import path
from .views import ProcessDataAgentView, LatestProcessDataFrontendView, ListHostsView , SystemInfoFrontendView , ProcessMonitorView ,sockets_test , host_monitor_view 
from .views import sockets_test, host_monitor_view
from . import views

urlpatterns = [
    path('agent/process-data/', ProcessDataAgentView.as_view(), name='agent-process-data'),
    path('frontend/hosts/', ListHostsView.as_view(), name='list-hosts'),
    path('frontend/processes/<str:hostname>/', LatestProcessDataFrontendView.as_view(), name='frontend-processes-by-hostname'),
    path('frontend/system-info/<str:hostname>/', SystemInfoFrontendView.as_view(), name='frontend-system-info'),
    path('', ProcessMonitorView.as_view(), name='process-monitor'),
    
    # implementation of the sockets test view
    # path('sockets_test/', sockets_test, name='sockets-test'),
    path('host-monitor/', views.host_monitor_view, name='host-monitor'),
    

]