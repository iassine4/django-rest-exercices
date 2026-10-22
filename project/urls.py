from rest_framework import routers
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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
    # Le jeton d'accès authentifie les requêtes ; le refresh permet de le renouveler.
    path('api/token/', TokenObtainPairView.as_view(), name='obtain_tokens'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('api/', include(router.urls))
]
