from rest_framework import status
from utilities.testing import APITestCase
from utilities.testing.utils import disable_warnings

from service_specification.models import Lifecycle


class LifecycleAPITestCase(APITestCase):
    """POST -> GET -> PATCH -> DELETE round trip against the plugin's REST
    API, using Lifecycle since it's the one model with no required related
    objects to create first. This exercises the real serializer/viewset/
    permission stack end to end, complementing test_models.py's plain ORM
    coverage.
    """

    model = Lifecycle
    # APITestCase._get_view_namespace() defaults to f'{app_label}-api',
    # which matches how *core* NetBox apps are mounted directly under
    # /api/. Plugins are mounted one level deeper (netbox/plugins/urls.py:
    # /api/plugins/ -> namespace 'plugins-api' -> namespace '<app_label>-api'),
    # so the default guess resolves to 'service_specification-api' when the real registered
    # namespace is 'plugins-api:service_specification-api'. Since view_namespace gets '-api'
    # appended automatically, 'plugins-api:service_specification' here becomes exactly that.
    view_namespace = 'plugins-api:service_specification'
    user_permissions = (
        'service_specification.add_lifecycle',
        'service_specification.view_lifecycle',
        'service_specification.change_lifecycle',
        'service_specification.delete_lifecycle',
    )

    def test_post_get_patch_delete(self):
        url = self._get_list_url()

        # POST: create a new Lifecycle
        response = self.client.post(url, {'name': 'Pilot', 'slug': 'pilot'}, format='json', **self.header)
        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        lifecycle_id = response.data['id']

        # GET: retrieve it back and confirm the data round-tripped
        detail_url = self._get_detail_url(Lifecycle.objects.get(pk=lifecycle_id))
        response = self.client.get(detail_url, **self.header)
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Pilot')
        self.assertEqual(response.data['slug'], 'pilot')

        # PATCH: change a field and confirm it actually persisted (not just
        # echoed back in the response)
        response = self.client.patch(
            detail_url,
            {'description': 'Pilot phase lifecycle stage'},
            format='json',
            **self.header,
        )
        self.assertHttpStatus(response, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Pilot phase lifecycle stage')
        self.assertEqual(
            Lifecycle.objects.get(pk=lifecycle_id).description,
            'Pilot phase lifecycle stage',
        )

        # DELETE: clean up
        response = self.client.delete(detail_url, **self.header)
        self.assertHttpStatus(response, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lifecycle.objects.filter(pk=lifecycle_id).exists())

    def test_create_without_permission_is_rejected(self):
        # Same POST as above, but as a user with no service_specification.add_lifecycle
        # permission — the base APITestCase.setUp() already grants
        # user_permissions, so this simulates the anonymous/unauthorized
        # case by clearing them first.
        self.user.object_permissions.all().delete()
        with disable_warnings('django.request'):
            response = self.client.post(
                self._get_list_url(),
                {'name': 'Should Not Be Created', 'slug': 'nope'},
                format='json',
                **self.header,
            )
        self.assertHttpStatus(response, status.HTTP_403_FORBIDDEN)
