class CompareBoundField(object):
    """
    Just like django.forms.BoundField, this class corresponds for
    storing field and associated data

        ``comparator`` object of comparator
        ``field`` comparator field
        ``name`` field name
        ``is_related`` True if field is M2M, O2O, FK fields

    Usage:
         - get values from comparator by field's name
         - pass those values to field by differ method

        ``differ()`` method that calls field's differ method with value, to count differences
    """
    comparator = None
    field = None

    def __init__(self, comparator, field, name, is_related=False):
        self.comparator = comparator
        self.field = field
        self.name = name
        self.is_related = is_related

        self.first = self.comparator.get_first_field_value(self.name)
        self.second = self.comparator.get_second_field_value(self.name)
        self.differences = self.differ()

    def __str__(self):
        return self.render()

    def differ(self):
        return self.field.differ(self.first, self.second)

    def differ_fields(self):
        return self.field.differ_fields(self.first, self.second)

    def render(self):
        if self.is_related:
            return self.field.widget.render(self.field.get_related_comparator(), self.differences, self.field.label)

        return self.field.widget.render(self.first, self.second, self.differences, self.field.label)
