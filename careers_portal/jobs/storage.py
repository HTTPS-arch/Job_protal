from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """Uploaded files (resumes) ko database mein rakhta hai.

    Render free plan pe disk persistent nahi hota, isliye media/ folder
    redeploy ya restart pe ud jata hai. Files DB mein rahengi toh bachi rahengi.
    """

    def _model(self):
        from .models import StoredFile  # lazy import, circular import se bachne ke liye
        return StoredFile

    def _open(self, name, mode='rb'):
        try:
            obj = self._model().objects.get(name=name)
        except self._model().DoesNotExist:
            raise FileNotFoundError(name)
        return ContentFile(bytes(obj.content), name=name)

    def _save(self, name, content):
        content.seek(0)
        self._model().objects.create(name=name, content=content.read())
        return name

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def delete(self, name):
        self._model().objects.filter(name=name).delete()

    def size(self, name):
        return len(self._model().objects.get(name=name).content)

    # url() jaan-boojh ke implement nahi kiya: resume sirf admin download view se milegi.
