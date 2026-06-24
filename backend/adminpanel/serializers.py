"""
Dynamic ModelSerializer factory for admin-panel resources.

Each resource's serializer is built on the fly from its registry config
rather than hand-written, since every resource follows the same shape
(some fields editable, some read-only). Foreign-key fields additionally get
a companion "<field>_label" string so the frontend table/form can show a
human-readable value (e.g. a user's email) instead of a bare numeric id,
while the raw id remains read/writable for actual edits.
"""

from rest_framework import serializers


def _display_value(obj):
    if obj is None:
        return None
    for attr in ("reference", "case_id", "transaction_id", "email", "title", "label", "company_name", "name"):
        value = getattr(obj, attr, None)
        if value:
            return value
    return str(obj)


def build_serializer(config):
    model = config["model"]
    all_fields = list(dict.fromkeys(config["readonly_fields"] + config["editable_fields"]))

    relation_names = {
        f.name for f in model._meta.get_fields()
        if getattr(f, "is_relation", False) and not f.many_to_many and not f.one_to_many
    }
    fk_fields = [name for name in all_fields if name in relation_names]

    attrs = {}
    extra_field_names = []
    for name in fk_fields:
        label_name = f"{name}_label"
        extra_field_names.append(label_name)

        def make_getter(field_name):
            def getter(self, obj):
                return _display_value(getattr(obj, field_name))
            return getter

        attrs[label_name] = serializers.SerializerMethodField()
        attrs[f"get_{label_name}"] = make_getter(name)

    class Meta:
        pass

    Meta.model = model
    Meta.fields = all_fields + extra_field_names
    Meta.read_only_fields = config["readonly_fields"] + extra_field_names
    attrs["Meta"] = Meta

    return type(f"{model.__name__}AdminSerializer", (serializers.ModelSerializer,), attrs)
