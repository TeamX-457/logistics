from django.conf import settings
from django.db import models


class PriorityList(models.Model):
    driver = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="priority_entry",
        on_delete=models.CASCADE,
        limit_choices_to={"role": "driver"},
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="priority_additions", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Priority: {self.driver}"
