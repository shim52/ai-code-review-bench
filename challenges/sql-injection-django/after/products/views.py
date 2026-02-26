from django.db import connection
from django.http import JsonResponse
from django.views import View


class ProductListView(View):
    """List all products."""

    def get(self, request):
        from .models import Product

        products = Product.objects.all()[:50]
        data = [{"id": p.id, "name": p.name, "price": str(p.price)} for p in products]
        return JsonResponse({"products": data})


class ProductSearchView(View):
    """Search products by name and category."""

    def get(self, request):
        name = request.GET.get("name", "")
        category = request.GET.get("category", "")

        with connection.cursor() as cursor:
            query = f"""
                SELECT id, name, price, category
                FROM products_product
                WHERE name LIKE '%{name}%'
                AND category = '{category}'
            """
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return JsonResponse({"results": results})
