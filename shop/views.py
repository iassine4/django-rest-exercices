from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action

from shop.models import Category, Product, Article
from shop.permissions import IsAdminAuthenticated, IsStaffAuthenticated
from shop.serializers import (
    CategoryDetailSerializer, CategoryListSerializer,
    ProductDetailSerializer, ProductListSerializer, ArticleSerializer,
)


class MultipleSerializerMixin:
    """Choisit une représentation détaillée pour la consultation d'un objet."""

    detail_serializer_class = None

    def get_serializer_class(self):
        # retrieve correspond à GET /ressource/<id>/ ; list à GET /ressource/.
        if self.action == 'retrieve' and self.detail_serializer_class is not None:
            return self.detail_serializer_class
        return super().get_serializer_class()


class AdminCategoryViewset(MultipleSerializerMixin, ModelViewSet):
    """Permet de consulter, créer, modifier et supprimer toutes les catégories."""

    serializer_class = CategoryListSerializer
    detail_serializer_class = CategoryDetailSerializer
    queryset = Category.objects.all()
    # Les permissions de cette liste doivent toutes être satisfaites (ET).
    permission_classes = [IsAdminAuthenticated, IsStaffAuthenticated]


class CategoryViewset(MultipleSerializerMixin, ReadOnlyModelViewSet):
    """Expose les catégories actives en lecture, avec une action de désactivation."""

    serializer_class = CategoryListSerializer
    detail_serializer_class = CategoryDetailSerializer

    def get_queryset(self):
        return Category.objects.filter(active=True)

    @action(detail=True, methods=['post'])
    def disable(self, request, pk):
        """Traite POST /api/category/<id>/disable/."""
        # get_object() renvoie une erreur 404 si la catégorie est absente ou inactive.
        self.get_object().disable()
        return Response()


class ProductViewset(MultipleSerializerMixin, ReadOnlyModelViewSet):
    """Expose les produits actifs et permet leur désactivation."""

    serializer_class = ProductListSerializer
    detail_serializer_class = ProductDetailSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(active=True)
        # Le paramètre facultatif ?category_id=... restreint la liste à une catégorie.
        category_id = self.request.GET.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=True, methods=['post'])
    def disable(self, request, pk):
        """Traite POST /api/product/<id>/disable/."""
        self.get_object().disable()
        return Response()


class ArticleViewset(ReadOnlyModelViewSet):
    """Expose les articles actifs, éventuellement filtrés par product_id."""

    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = Article.objects.filter(active=True)
        product_id = self.request.GET.get('product_id')
        if product_id is not None:
            queryset = queryset.filter(product_id=product_id)
        return queryset


class AdminArticleViewset(ModelViewSet):
    """Permet de consulter, créer, modifier et supprimer tous les articles."""

    serializer_class = ArticleSerializer
    queryset = Article.objects.all()
