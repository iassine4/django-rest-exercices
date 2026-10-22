from rest_framework import routers
from django.contrib import admin
from django.urls import path, include

from shop.views import (
    CategoryViewset, ProductViewset, ArticleViewset,
    AdminCategoryViewset, AdminArticleViewset,
)


# Le routeur génère les routes de liste, de détail et les actions des ViewSets.
router = routers.SimpleRouter()
router.register('category', CategoryViewset, basename='category')
router.register('product', ProductViewset, basename='product')
router.register('article', ArticleViewset, basename='article')

# Le préfixe admin distingue ces API de l'interface Django située sous /admin/.
router.register('admin/category', AdminCategoryViewset, basename='admin-category')
router.register('admin/article', AdminArticleViewset, basename='admin-article')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(router.urls))
]
