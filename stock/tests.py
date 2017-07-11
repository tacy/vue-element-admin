from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import PurchaseOrder
from django.core.urlresolvers import reverse


# Create your tests here.
class ModelTestCase(TestCase):
    """This class defines the test suite for the bucketlist model."""

    def setUp(self):
        """Define the test client and other test variables."""
        self.po_name = "Write world class code"
        self.po = PurchaseOrder(name=self.po_name)

    def test_model_can_create_a_po(self):
        """Test the purchaseorder model can create a po."""
        old_count = PurchaseOrder.objects.count()
        self.po.save()
        new_count = PurchaseOrder.objects.count()
        self.assertNotEqual(old_count, new_count)


# Define this after the ModelTestCase
class ViewTestCase(TestCase):
    """Test suite for the api views."""

    def setUp(self):
        """Define the test client and other test variables."""
        self.client = APIClient()
        self.po_data = {'name': 'Go to Ibiza'}
        self.response = self.client.post(
            reverse('create'),
            self.po_data,
            format="json")

    def test_api_can_create_a_po(self):
        """Test the api has po creation capability."""
        self.assertEqual(self.response.status_code, status.HTTP_201_CREATED)

    def test_api_can_get_a_po(self):
        """Test the api can get a given po."""
        po = PurchaseOrder.objects.get()
        response = self.client.get(
            reverse('details', kwargs={'pk': po.id}), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, po)

    def test_api_can_update_po(self):
        """Test the api can update a given po."""
        change_po = {'name': 'Something new'}
        po = PurchaseOrder.objects.get()
        res = self.client.put(
            reverse('details', kwargs={'pk': po.id}),
            change_po, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_api_can_delete_po(self):
        """Test the api can delete a po."""
        po = PurchaseOrder.objects.get()
        response = self.client.delete(
            reverse('details', kwargs={'pk': po.id}), format='json', follow=True)

        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
