from decimal import Decimal
from unittest import mock

import requests

from django.urls import reverse_lazy, reverse
from rest_framework.test import APITestCase

from shop.models import Category, Product, Article


class ShopAPITestCase(APITestCase):
    """Partage les données et représentations attendues sur une base de test isolée."""

    def setUp(self):
        super().setUp()
        # Aucun test d'API ne dépend du réseau ou de la disponibilité du service.
        patcher = mock.patch('shop.models.Product.call_external_api')
        self.external_api = patcher.start()
        self.addCleanup(patcher.stop)
        self.external_api.return_value = mock.Mock(status_code=200)
        self.external_api.return_value.json.return_value = {'product': {'ecoscore_grade': 'a'}}

    @classmethod
    def setUpTestData(cls):
        """Prépare des éléments actifs et inactifs pour vérifier les filtres."""
        cls.category = Category.objects.create(name='Fruits', active=True)
        Category.objects.create(name='Légumes', active=False)

        cls.product = cls.category.products.create(name='Ananas', active=True)
        cls.category.products.create(name='Banane', active=False)

        cls.category_2 = Category.objects.create(name='Légumes', active=True)
        cls.product_2 = cls.category_2.products.create(name='Tomate', active=True)

        cls.article = cls.product.articles.create(name='Ananas pièce', price=Decimal('2.50'), active=True)
        cls.product.articles.create(name='Ananas inactif', price=Decimal('3.00'), active=False)
        cls.article_2 = cls.product_2.articles.create(name='Tomate pièce', price=Decimal('1.20'), active=True)

    def format_datetime(self, value):
        """Reproduit le format UTC utilisé dans les réponses JSON de l'API."""
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def get_article_list_data(self, articles):
        return [
            {
                'id': article.pk,
                'name': article.name,
                'date_created': self.format_datetime(article.date_created),
                'date_updated': self.format_datetime(article.date_updated),
                'price': format(article.price, '.2f'),
                'product': article.product_id,
            } for article in articles
        ]

    def get_product_list_data(self, products):
        return [
            {
                'id': product.pk,
                'name': product.name,
                'date_created': self.format_datetime(product.date_created),
                'date_updated': self.format_datetime(product.date_updated),
                'category': product.category_id,
                'ecoscore': 'a',
            } for product in products
        ]


class TestCategory(ShopAPITestCase):
    """Vérifie la lecture des catégories et les effets de leur désactivation."""

    url = reverse_lazy('category-list')

    def test_disable(self):
        url = reverse('category-disable', kwargs={'pk': self.category.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertFalse(self.category.active)
        self.assertFalse(self.category.products.filter(active=True).exists())
        self.product.refresh_from_db()
        self.assertFalse(self.product.active)
        self.category_2.refresh_from_db()
        self.product_2.refresh_from_db()
        self.assertTrue(self.category_2.active)
        self.assertTrue(self.product_2.active)
        # Comme dans le cours, la désactivation d'une catégorie ne modifie pas les articles.
        self.article.refresh_from_db()
        self.assertTrue(self.article.active)
        response = self.client.get(self.url)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'][0]['id'], self.category_2.pk)
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_disable_get_not_allowed(self):
        response = self.client.get(reverse('category-disable', kwargs={'pk': self.category.pk}))
        self.assertEqual(response.status_code, 405)
        self.category.refresh_from_db()
        self.assertTrue(self.category.active)

    def test_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        expected = [
            {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'date_created': self.format_datetime(category.date_created),
                'date_updated': self.format_datetime(category.date_updated),
            } for category in [self.category, self.category_2]
        ]
        self.assertEqual(response.json()['results'], expected)
        self.assertEqual(response.json()['count'], 2)
        self.assertIsNone(response.json()['next'])
        self.assertIsNone(response.json()['previous'])

    def test_create(self):
        category_count = Category.objects.count()
        response = self.client.post(self.url, data={'name': 'Nouvelle catégorie'})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Category.objects.count(), category_count)

    def test_detail(self):
        response = self.client.get(reverse('category-detail', kwargs={'pk': self.category.pk}))
        self.assertEqual(response.status_code, 200)
        expected = {
            'id': self.category.pk,
            'name': self.category.name,
            'date_created': self.format_datetime(self.category.date_created),
            'date_updated': self.format_datetime(self.category.date_updated),
            'products': self.get_product_list_data([self.product]),
        }
        self.assertEqual(response.json(), expected)


class TestProduct(ShopAPITestCase):
    """Vérifie les produits, leurs filtres, la pagination et leur désactivation."""

    url = reverse_lazy('product-list')

    def test_disable(self):
        url = reverse('product-disable', kwargs={'pk': self.product.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.article.refresh_from_db()
        self.assertFalse(self.product.active)
        self.assertFalse(self.article.active)
        self.assertFalse(self.product.articles.filter(active=True).exists())
        self.category.refresh_from_db()
        self.product_2.refresh_from_db()
        self.article_2.refresh_from_db()
        self.assertTrue(self.category.active)
        self.assertTrue(self.product_2.active)
        self.assertTrue(self.article_2.active)
        response = self.client.get(self.url)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['results'], self.get_product_list_data([self.product_2]))
        self.assertEqual(self.client.post(url).status_code, 404)

    def test_disable_get_not_allowed(self):
        response = self.client.get(reverse('product-disable', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 405)
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)

    def test_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_product_list_data([self.product, self.product_2]), response.json()['results'])

    def test_list_filter(self):
        response = self.client.get(self.url, {'category_id': self.category.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_product_list_data([self.product]), response.json()['results'])
        self.assertEqual(response.json()['count'], 1)

    def test_pagination(self):
        self.category.products.create(name='Orange', active=True)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        self.assertEqual(len(response.json()['results']), 2)
        self.assertIsNotNone(response.json()['next'])
        self.assertIsNone(response.json()['previous'])

        response = self.client.get(self.url, {'limit': 1, 'offset': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 3)
        self.assertEqual(response.json()['results'], self.get_product_list_data([self.product_2]))
        self.assertIsNotNone(response.json()['next'])
        self.assertIsNotNone(response.json()['previous'])

    def test_list_when_external_api_is_unavailable(self):
        self.external_api.side_effect = requests.Timeout('Service indisponible')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 2)
        expected = self.get_product_list_data([self.product, self.product_2])
        for product in expected:
            product['ecoscore'] = None
        self.assertEqual(response.json()['results'], expected)

    def test_detail(self):
        response = self.client.get(reverse('product-detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 200)
        expected = self.get_product_list_data([self.product])[0]
        # Comme dans le cours, seul le serializer de liste expose l'écoscore.
        expected.pop('ecoscore')
        expected['articles'] = self.get_article_list_data([self.article])
        self.assertEqual(response.json(), expected)

    def test_create(self):
        product_count = Product.objects.count()
        response = self.client.post(self.url, data={'name': 'Nouveau produit'})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Product.objects.count(), product_count)

    def test_delete(self):
        response = self.client.delete(reverse('product-detail', kwargs={'pk': self.product.pk}))
        self.assertEqual(response.status_code, 405)
        self.product.refresh_from_db()


class TestAdminCategory(ShopAPITestCase):
    """Vérifie les opérations d'écriture et les validations des catégories."""

    url = reverse_lazy('admin-category-list')

    def test_list_includes_inactive(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Category.objects.count())
        inactive = Category.objects.get(active=False)
        response = self.client.get(reverse('admin-category-detail', kwargs={'pk': inactive.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], inactive.pk)

    def test_create_update_delete(self):
        response = self.client.post(self.url, {'name': 'Boissons', 'description': 'Boissons fraîches'})
        self.assertEqual(response.status_code, 201)
        category = Category.objects.get(pk=response.json()['id'])
        self.assertEqual(category.name, 'Boissons')
        self.assertEqual(category.description, 'Boissons fraîches')
        url = reverse('admin-category-detail', kwargs={'pk': category.pk})

        # Un PUT avec le même nom doit rester valide.
        response = self.client.put(url, {'name': 'Boissons', 'description': 'Boissons chaudes'})
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.description, 'Boissons chaudes')

        response = self.client.patch(url, {'description': 'Boissons variées'})
        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertEqual(category.name, 'Boissons')
        self.assertEqual(category.description, 'Boissons variées')

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(pk=category.pk).exists())

    def test_invalid_create_does_not_save(self):
        category_count = Category.objects.count()
        cases = [
            ({'name': 'Fruits', 'description': 'Fruits frais'}, 'name'),
            ({'name': 'Boissons', 'description': 'Sans le nom'}, 'non_field_errors'),
            ({'name': 'Boissons'}, 'non_field_errors'),
            ({}, 'name'),
        ]
        for data, error_field in cases:
            with self.subTest(data=data):
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(error_field, response.json())
                self.assertEqual(Category.objects.count(), category_count)

    def test_partial_update_validates_combined_data(self):
        category = Category.objects.create(name='Boissons', description='Boissons fraîches')
        url = reverse('admin-category-detail', kwargs={'pk': category.pk})
        for data in [{'name': 'Fruits'}, {'name': 'Jus'}, {'description': 'Sans le nom'}]:
            with self.subTest(data=data):
                response = self.client.patch(url, data)
                self.assertEqual(response.status_code, 400)
                category.refresh_from_db()
                self.assertEqual(category.name, 'Boissons')
                self.assertEqual(category.description, 'Boissons fraîches')

        # Le nom omis est repris depuis l'instance, ainsi que la description omise.
        response = self.client.patch(url, {'name': 'Boissons'})
        self.assertEqual(response.status_code, 200)


class TestAdminArticle(ShopAPITestCase):
    """Vérifie les opérations d'écriture et les validations des articles."""

    url = reverse_lazy('admin-article-list')

    def test_list_includes_inactive(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], Article.objects.count())
        inactive = Article.objects.get(active=False)
        response = self.client.get(reverse('admin-article-detail', kwargs={'pk': inactive.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), self.get_article_list_data([inactive])[0])

    def test_create_update_delete(self):
        response = self.client.post(self.url, {
            'name': 'Ananas nouveau', 'price': '1.00', 'product': self.product.pk,
        })
        self.assertEqual(response.status_code, 201)
        article = Article.objects.get(pk=response.json()['id'])
        self.assertEqual(article.price, Decimal('1.00'))
        url = reverse('admin-article-detail', kwargs={'pk': article.pk})

        response = self.client.put(url, {
            'name': 'Tomate nouvelle', 'price': '2.50', 'product': self.product_2.pk,
        })
        self.assertEqual(response.status_code, 200)
        article.refresh_from_db()
        self.assertEqual(article.name, 'Tomate nouvelle')
        self.assertEqual(article.product_id, self.product_2.pk)

        response = self.client.patch(url, {'price': '3.00'})
        self.assertEqual(response.status_code, 200)
        article.refresh_from_db()
        self.assertEqual(article.price, Decimal('3.00'))

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Article.objects.filter(pk=article.pk).exists())

    def test_invalid_create_does_not_save(self):
        inactive_product = Product.objects.get(active=False)
        article_count = Article.objects.count()
        cases = [
            ({'name': 'Article', 'price': '0.99', 'product': self.product.pk}, 'price'),
            ({'name': 'Article', 'price': '2.00', 'product': inactive_product.pk}, 'product'),
            ({}, 'name'),
        ]
        for data, error_field in cases:
            with self.subTest(data=data):
                response = self.client.post(self.url, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn(error_field, response.json())
                self.assertEqual(Article.objects.count(), article_count)

    def test_invalid_update_does_not_save(self):
        inactive_product = Product.objects.get(active=False)
        url = reverse('admin-article-detail', kwargs={'pk': self.article.pk})
        for data in [{'price': '0.99'}, {'product': inactive_product.pk}]:
            with self.subTest(data=data):
                response = self.client.patch(url, data)
                self.assertEqual(response.status_code, 400)
                self.article.refresh_from_db()
                self.assertEqual(self.article.price, Decimal('2.50'))
                self.assertEqual(self.article.product_id, self.product.pk)


class TestProductEcoscore(APITestCase):
    """Vérifie l'intégration externe sans envoyer de requête HTTP réelle."""

    def test_success(self):
        response = mock.Mock(status_code=200)
        response.json.return_value = {'product': {'ecoscore_grade': 'b'}}
        product = Product(name='Produit de test')
        with mock.patch.object(product, 'call_external_api', return_value=response) as external_api:
            self.assertEqual(product.ecoscore, 'b')
        external_api.assert_called_once_with(
            'GET', 'https://world.openfoodfacts.org/api/v0/product/3229820787015.json',
        )

    def test_http_error(self):
        for status_code in [404, 503]:
            with self.subTest(status_code=status_code):
                response = mock.Mock(status_code=status_code)
                with mock.patch.object(Product, 'call_external_api', return_value=response):
                    self.assertIsNone(Product().ecoscore)
                response.json.assert_not_called()

    def test_network_error(self):
        for error in [requests.Timeout('Timeout'), requests.ConnectionError('Connexion impossible')]:
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(Product, 'call_external_api', side_effect=error):
                    self.assertIsNone(Product().ecoscore)

    def test_missing_data(self):
        for data in [{}, {'product': {}}, {'product': None}, {'product': []}, None, []]:
            with self.subTest(data=data):
                response = mock.Mock(status_code=200)
                response.json.return_value = data
                with mock.patch.object(Product, 'call_external_api', return_value=response):
                    self.assertIsNone(Product().ecoscore)

    def test_invalid_json(self):
        response = mock.Mock(status_code=200)
        response.json.side_effect = ValueError('JSON invalide')
        with mock.patch.object(Product, 'call_external_api', return_value=response):
            self.assertIsNone(Product().ecoscore)

    def test_request_has_timeout(self):
        with mock.patch('shop.models.requests.request') as request:
            response = Product().call_external_api('GET', 'https://example.com')
        request.assert_called_once_with('GET', 'https://example.com', timeout=5)
        self.assertIs(response, request.return_value)
