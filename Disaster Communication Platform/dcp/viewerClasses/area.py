from django.views.generic import View
from django.views.static import loader
from django.shortcuts import get_object_or_404
from dcp.viewerClasses.organization import OrganizationView
from dcp.models.organizations import *
from dcp.customForms.organizationForms import AreaForm, NgoForm, GovernmentAreaForm, NgoAreaForm, AddNgoForm, AddGovernmentForm
from django.http.response import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from geopy.geocoders import Nominatim
from django.core.urlresolvers import reverse
from dcp.customclasses.distance.distance import calculateDistanceClass

class AreaView(LoginRequiredMixin, View):
    def get(self, request, pk, subAreaForm=None):
        user = request.user
        # TODO Permissons
        templatePath = 'dcp/content/organization/area.html'
        template = loader.get_template(templatePath)
        area = get_object_or_404(Area.objects.select_related('catastrophe').prefetch_related('government_set', 'ngo_set', 'ngoarea_set', 'governmentarea_set') , id=pk)

        if subAreaForm == None: # Add Permissions
            subAreaForm = AreaForm

        if True: # TODO Permissons
            addNgoForm = AddNgoForm()
            ngos = Ngo.objects.exclude(areas=area)
            ngoChoices = []
            for ngo in ngos:
                ngoChoices.append((ngo.id, ngo.name))
            addNgoForm['ngo'].field.choices = ngoChoices
        else :
            addNgoForm = None

        if True: # TODO Permissons
            addGovernmentForm = AddGovernmentForm()
            governments = Government.objects.exclude(areas=area)
            governmentChoices = []
            for government in governments:
                governmentChoices.append((government.id, government.name))
            addGovernmentForm['government'].field.choices = governmentChoices
        else:
            addGovernmentForm = None


        # TODO Permissions
        canDeleteArea = True

        allNgoAreas = area.ngoarea_set.all()
        allGovernmentAreas = area.governmentarea_set.all()

        ngoAreaFormList = []
        ngoAreaList = []
        for ngoArea in allNgoAreas:
            ngoAreaList.append(ngoArea)
            form = NgoAreaForm(ngoAreaQuery=allNgoAreas, ngoArea=ngoArea)
            ngoAreaFormList.append(form)

        ngoAreaFormList = zip(ngoAreaList, ngoAreaFormList)
            
        governmentAreaFormList = []
        governmentAreaList = []
        for governmentArea in allGovernmentAreas:
            governmentAreaList.append(governmentArea)
            form = GovernmentAreaForm(governmentAreaQuery=allGovernmentAreas, governmentArea=governmentArea)
            governmentAreaFormList.append(form)

        governmentAreaFormListZipped = zip(governmentAreaList, governmentAreaFormList)

        context = {
            'area' : area,
            'addNgoForm': addNgoForm,
            'addGovernmentForm': addGovernmentForm,
            'subAreaForm' : subAreaForm,
            'canDeleteArea' : canDeleteArea,
            'ngoAreaFormList' : ngoAreaFormList,
            'governmentAreaFormList' : governmentAreaFormListZipped
            
        }
        return HttpResponse(template.render(context, request))

    def post(self, request, pk):
        # TODO Permissons
        user = request.user
        post_identifier = request.POST.get('post_identifier')
        area = get_object_or_404(Area.objects.select_related('catastrophe').prefetch_related('government_set', 'ngo_set', 'ngoarea_set', 'governmentarea_set') , id=pk)

        if post_identifier == 'degrateGovernment': # TODO Permissons
            pass
        if post_identifier == 'promoteGovernment': # TODO Permissons
            pass
        if post_identifier == 'degrateNgo': # TODO Permissons
            pass
        if post_identifier == 'promoteNgo': # TODO Permissons
            pass

        if post_identifier == 'addSubArea': # TODO Permissons
            successCreate, obj = createArea(request, parrentArea=area)
            if successCreate:
                return obj
            else:
                return self.get(request, pk, subAreaForm=obj)

        if post_identifier == 'addNgo': # TODO Permissons
            form = AddNgoForm(request.POST)
            if form.is_valid():
                NgoArea.objects.create(ngo=form.cleaned_data['ngo'], area=area)
            else:
                print(form.errors)
            return self.get(request, pk)

        if post_identifier == 'addGovernment': # TODO Permissons
            form = AddGovernmentForm(request.POST)
            if form.is_valid():
                GovernmentArea.objects.create(government=form.cleaned_data['government'], area=area)
            return self.get(request, pk)

        if post_identifier == 'deleteArea': # TODO Permissons
            area.delete()
            return HttpResponseRedirect('/')

class AreaAdminView(LoginRequiredMixin,View):
    def get(self, request, create_new_form=AreaForm):
        user = request.user
        catastrophe = user.profile.currentCatastrophe
        if not user.is_superuser:
            return HttpResponseForbidden("Insufficent rights")
        templatePath = 'dcp/content/organization/areaAdmin.html'
        template = loader.get_template(templatePath)
        if catastrophe is not None:
            area_list = Area.objects.filter(catastrophe=catastrophe).order_by('created_date').reverse().select_related('catastrophe').prefetch_related('ngo_set','government_set').reverse()
        else: 
            area_list = Area.objects.all().order_by('created_date').reverse().select_related('catastrophe').prefetch_related('ngo_set','government_set')

        context = {
            'area_list': area_list,
            'create_new_form' : create_new_form
        }
        return HttpResponse(template.render(context, request))

    def post(self, request):
        user = request.user
        if not user.is_superuser:
            return HttpResponseForbidden("Insufficent rights")
        
        successCreate, obj = createArea(request)
        if successCreate:
            return obj
        else:
            return self.get(request, create_new_form=obj)

def createArea(request, parrentArea:Area=None):
        form = AreaForm(request.POST)
        if form.is_valid():
            area = form.save(commit=False)

            try :
                geolocator = Nominatim()
                location = geolocator.reverse(str(area.location_x) + " , " + str(area.location_y))
                area.locationString = location.address
            except:
                area.locationString = " "

            area.parrent = parrentArea
            
            # TODO Verifiziere die Distanzberechnung
            if parrentArea:
                parrentDistance = calculateDistanceClass.calculate_distance(parrentArea.location_x, parrentArea.location_y, area.location_x, area.location_y)
                maxOutsideRadius = parrentArea.radius + parrentArea.maxOutsideRadius
            else :
                parrentDistance = calculateDistanceClass.calculate_distance(area.catastrophe.location_x, area.catastrophe.location_y, area.location_x, area.location_y)
                maxOutsideRadius = area.catastrophe.radius + area.catastrophe.maxOutsideRadius

            if (parrentDistance + area.radius) >= maxOutsideRadius:
                form.add_error('radius', "Bitte wähle ein Gebiet näher an dem Überliegenden")
                return (False, form)

            if (parrentDistance + area.radius + area.maxOutsideRadius) >= maxOutsideRadius:
                area.maxOutsideRadius = (maxOutsideRadius - parrentDistance)
                
            area.save()

            ngos = Ngo.objects.filter(id__in=request.POST.getlist('ngos'))
            createNgoAreas = []
            for ngo in ngos:
                createNgoAreas.append(NgoArea(ngo=ngo, area=area))

            governments = Government.objects.filter(id__in=request.POST.getlist('governments'))
            createGovernmentsAreas = []
            for government in governments:
                createGovernmentsAreas.append(GovernmentArea(government=government, area=area))
            NgoArea.objects.bulk_create(createNgoAreas)
            GovernmentArea.objects.bulk_create(createGovernmentsAreas)
            return (True, HttpResponseRedirect(reverse('dcp:AreaView', kwargs={'pk':area.id})))
        else:
            return (False, form)