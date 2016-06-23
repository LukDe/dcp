# imports
from dcp.importUrls import *
from dcp.viewerClasses.timeline import *

class Index(TimelineView):

	def get(self, request):
		countSearch = len(dcp.models.Search_Material.objects.all()) + len(dcp.models.Search_Immaterial.objects.all())
		countOffer = len(dcp.models.Offer_Material.objects.all()) + len(dcp.models.Offer_Immaterial.objects.all())
		countInformation = 0 # TODO
		countPeople = len(MissedPeople.objects.all())
		
		# user = request.user und irgendwas wie .filter(user=user) fehlt noch...
		goods_list = sorted(Goods.getAllGoods(), key=lambda g: g.created_date, reverse=True)
		goods_list = filter(lambda x: x.user==request.user, goods_list)

		panel_title = "Übersicht  deiner erstellten Gesuche und Angebote"

		template = 'dcp/index.html'
		params = {
				'goods_list': goods_list,
				'countSearch': countSearch,
				'countOffer': countOffer,
				'countInformation': countInformation,
				'countPeople': countPeople,
				'panel_title': panel_title
		}
		return dcp.viewerClasses.authentication.getPageAuthenticated(request, template, params)

	def post(self, request):
		return super().post(request)