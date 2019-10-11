import copy

from compare.meta import model_to_dict, ModelComparatorMetaclass


class BaseModelComparator(object):
    """
        BaseModelComparator

        ``first``, ``second`` - objects to compare
    """
    bound_fields_cache = None

    def __init__(self, first, second):
        opts = self._meta
        if opts.model is None:
            raise ValueError('ModelComparator has no model class specified.')

        self.bound_fields_cache = {}
        self.fields = copy.deepcopy(self.base_fields)

        self.first, self.second = first, second
        self.first_object_data = model_to_dict(self.first, opts.fields, opts.exclude)
        self.second_object_data = model_to_dict(self.second, opts.fields, opts.exclude)

    def __getitem__(self, item):
        return self.get_bound_field(item)

    def __iter__(self):
        for name in self.fields:
            yield self[name]

    def compare(self):
        differences = 0
        for name, field in self.fields.items():
            field = self.get_bound_field(name)
            if field:
                differs = field.differ()
                differences += differs if differs else 0

        return differences

    def compare_fields(self):
        fields = []
        for name, field in self.fields.items():
            bound_field = self.get_bound_field(name)
            fields.extend(bound_field.differ_fields())

        return fields

    def get_bound_field(self, name):
        field = self.fields[name]

        if name not in self.bound_fields_cache:
            self.bound_fields_cache[name] = field.get_bound_field(self)
        return self.bound_fields_cache[name]

    def get_first_field_value(self, field_name):
        """Used by bound field to get values"""
        return self.first_object_data.get(field_name)

    def get_second_field_value(self, field_name):
        """Used by bound field to get values"""
        return self.second_object_data.get(field_name)

    def get_first(self):
        return self.first

    def get_second(self):
        return self.first


class ModelComparator(BaseModelComparator, metaclass=ModelComparatorMetaclass):
    pass
