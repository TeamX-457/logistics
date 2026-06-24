"""
Builds frontend-facing field metadata (label, input type, choices, readonly)
for a resource by introspecting the underlying Django model fields. This lets
admin-panel.html render one generic edit form for any resource instead of
needing a hand-written form per model.
"""

from django.db import models as dj

_TYPE_MAP = (
    (dj.BooleanField, "boolean"),
    (dj.TextField, "textarea"),
    (dj.DateTimeField, "datetime"),
    (dj.DateField, "date"),
    (dj.EmailField, "email"),
    (dj.DecimalField, "number"),
    (dj.FloatField, "number"),
    (dj.IntegerField, "number"),
    (dj.ForeignKey, "fk"),
    (dj.OneToOneField, "fk"),
)


def _field_type(field):
    for cls, kind in _TYPE_MAP:
        if isinstance(field, cls):
            return kind
    return "text"


def build_field_schema(config):
    model = config["model"]
    readonly = set(config["readonly_fields"])
    order = list(dict.fromkeys(config["readonly_fields"] + config["editable_fields"]))
    schema = []
    for name in order:
        try:
            field = model._meta.get_field(name)
        except Exception:
            schema.append({
                "name": name,
                "label": name.replace("_", " ").title(),
                "type": "text",
                "readonly": name in readonly,
                "required": False,
                "choices": None,
            })
            continue
        choices = None
        if getattr(field, "choices", None):
            choices = [{"value": value, "label": label} for value, label in field.choices]
        schema.append({
            "name": name,
            "label": str(getattr(field, "verbose_name", name)).replace("_", " ").title(),
            "type": _field_type(field),
            "readonly": name in readonly,
            "required": not getattr(field, "blank", True) and not getattr(field, "null", True),
            "choices": choices,
        })
    return schema
