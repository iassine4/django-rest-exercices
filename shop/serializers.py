from rest_framework import serializers

from shop.models import Category, Product, Article


class ArticleSerializer(serializers.ModelSerializer):
    """Décrit les champs exposés d'un article et valide les données reçues."""

    class Meta:
        model = Article
        fields = ['id', 'date_created', 'date_updated', 'name', 'price', 'product']

    def validate_price(self, value):
        """Accepte les prix supérieurs ou égaux à 1."""
        if value < 1:
            raise serializers.ValidationError('Price must be at least 1')
        return value

    def validate_product(self, value):
        """Refuse de rattacher l'article à un produit inactif."""
        if value.active is False:
            raise serializers.ValidationError('Inactive product')
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Représentation légère des produits, sans leurs articles."""

    class Meta:
        model = Product
        fields = ['id', 'date_created', 'date_updated', 'name', 'category', 'ecoscore']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Ajoute les articles actifs au détail d'un produit."""

    # DRF appelle get_articles() pour calculer ce champ en lecture seule.
    articles = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'date_created', 'date_updated', 'name', 'category', 'articles']

    def get_articles(self, instance):
        queryset = instance.articles.filter(active=True)
        serializer = ArticleSerializer(queryset, many=True)
        return serializer.data


class CategoryListSerializer(serializers.ModelSerializer):
    """Expose les catégories en liste et valide leur création ou modification."""

    class Meta:
        model = Category
        fields = ['id', 'date_created', 'date_updated', 'name', 'description']

    def validate_name(self, value):
        """Vérifie l'unicité du nom en excluant la catégorie en cours de modification."""
        queryset = Category.objects.filter(name=value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('Category already exists')
        return value

    def validate(self, data):
        """Vérifie que la description contient le nom de la catégorie."""
        # En PATCH, les champs absents conservent la valeur de l'instance existante.
        name = data.get('name', getattr(self.instance, 'name', ''))
        description = data.get('description', getattr(self.instance, 'description', ''))
        if name not in description:
            raise serializers.ValidationError('Name must be in description')
        return data


class CategoryDetailSerializer(serializers.ModelSerializer):
    """Ajoute les produits actifs au détail d'une catégorie, sans leurs articles."""

    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'date_created', 'date_updated', 'name', 'products']

    def get_products(self, instance):
        queryset = instance.products.filter(active=True)
        serializer = ProductListSerializer(queryset, many=True)
        return serializer.data
