import json
import uuid

from django.db import models

from .utils import validate_advantage, validate_restrictions


class PromoCode(models.Model):
    name = models.CharField(max_length=255, unique=True)

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # advantage is a JSON field representing the associated advantage
    advantage = models.JSONField()

    # restrictions is JSON field representing the array of restrictions - see utils file for typing
    restrictions = models.JSONField()

    # Validation pre-save
    def save(self, *args, **kwargs):
        """
        Check that the promo code advantage and restrictions have a valid structure.
        Raise ValueError if not.
        """
        if isinstance(self.advantage, dict):
            advantage = self.advantage
        elif isinstance(self.advantage, str):
            try:
                advantage = json.loads(self.advantage)
            except json.JSONDecodeError:
                raise ValueError('advantage must be a valid JSON object.')
        else:
            raise ValueError('advantage must be a valid JSON object.')

        validation_err = validate_advantage(advantage)
        if validation_err:
            raise ValueError(validation_err)

        if isinstance(self.restrictions, list):
            restrictions = self.restrictions
        elif isinstance(self.restrictions, str):
            try:
                restrictions = json.loads(self.restrictions)
            except json.JSONDecodeError:
                raise ValueError('Restrictions must be a valid JSON object.')
        else:
            raise ValueError('Restrictions must be a valid JSON object.')

        validation_err = validate_restrictions(restrictions)
        if validation_err:
            raise ValueError(validation_err)

        super().save(*args, **kwargs)
