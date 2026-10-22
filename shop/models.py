import requests

from django.db import models, transaction


class Category(models.Model):
    """Regroupe des produits et conserve leur état d'activation."""

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    @transaction.atomic
    def disable(self):
        """Désactive la catégorie et ses produits dans une même transaction."""
        if self.active is False:
            return
        self.active = False
        self.save()
        # La mise à jour en lot ne déclenche pas Product.disable() ni celle des articles.
        self.products.update(active=False)


class Product(models.Model):
    """Produit rattaché à une catégorie et décliné en articles."""

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=False)

    category = models.ForeignKey('shop.Category', on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name

    @transaction.atomic
    def disable(self):
        """Désactive le produit et ses articles sans les supprimer."""
        if self.active is False:
            return
        self.active = False
        self.save()
        self.articles.update(active=False)

    def call_external_api(self, method, url):
        """Isole l'appel HTTP pour pouvoir le remplacer dans les tests."""
        return requests.request(method, url, timeout=5)

    @property
    def ecoscore(self):
        """Lit l'écoscore du produit de démonstration utilisé dans le cours."""
        # Le code-barres fixe est commun à tous les produits de cet exercice.
        url = 'https://world.openfoodfacts.org/api/v0/product/3229820787015.json'
        try:
            response = self.call_external_api('GET', url)
            if response.status_code != 200:
                return None
            data = response.json()
        except (requests.RequestException, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        product = data.get('product')
        if not isinstance(product, dict):
            return None
        return product.get('ecoscore_grade')


class Article(models.Model):
    """Déclinaison d'un produit avec son propre prix et état d'activation."""

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=4, decimal_places=2)

    product = models.ForeignKey('shop.Product', on_delete=models.CASCADE, related_name='articles')

    def __str__(self):
        return self.name
