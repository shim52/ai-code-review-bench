from django.http import JsonResponse
from django.views import View


class ProductListView(View):
    """List all products."""

    def get(self, request):
        from .models import Product

        products = Product.objects.all()[:50]
        data = [{"id": p.id, "name": p.name, "price": str(p.price)} for p in products]
        return JsonResponse({"products": data})
