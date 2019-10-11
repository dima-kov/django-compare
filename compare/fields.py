from django.db import models
from django.utils.translation import gettext as _

from compare.bound import CompareBoundField
from compare.widgets import CompareWidget, InternalCompareWidget, MultipleCompareWidget


class Decorators(object):
    @staticmethod
    def init_differ(decorated):
        def wrapper(self, first, second):
            self.first, self.second = first, second
            self._check_types()
            return decorated(self)

        return wrapper


class BaseCompareField(object):
    """
        BaseCompareField

        Field to:
            1. check comparing values types;
            2. Specify rendering widget
            3. Declare comparing process by the `_differ` method

        ``first``, ``second`` - values to compare. Are passed to field by differ method.
        ``name`` field name in model. Used When generating bound field
        ``is_related`` - is field represents M2M, O2O, FK.

        BoundField - single class that link field with data
    """

    first = None
    second = None
    name = None

    widget = None
    differs = None
    is_related = False

    def __init__(self, name, label):
        self.name = name
        self.label = label

    @Decorators.init_differ
    def differ(self):
        self.differs = self._differs()
        return self.differs

    @Decorators.init_differ
    def differ_fields(self):
        self.differs = self._differs()
        if self.differs > 0:
            return [self.label]
        return []

    def _check_types(self):
        nones = self.first is None or self.second is None
        different_types = type(self.first) != type(self.second)
        if different_types and not nones:
            raise ValueError(_(
                'Types of first and second comparing objects are not the same: {} vs {}'.format(
                    type(self.first), type(self.second)
                )
            ))

    def _differs(self):
        return 1 if not self.same() else 0

    def same(self):
        return self.first == self.second

    def get_bound_field(self, comparator):
        return CompareBoundField(comparator=comparator, field=self, name=self.name, is_related=self.is_related)


class CompareField(BaseCompareField):
    widget = CompareWidget()


class InternalFieldComparator(BaseCompareField):
    """
       FieldAsComparator - used for FK, O2O fields.

       You should pass a comparator class during init.
    """
    internal_comparator = None
    is_related = True
    widget = InternalCompareWidget()

    def __init__(self, name, label, related_comparator_class):
        super(InternalFieldComparator, self).__init__(name, label)
        self.related_comparator_class = related_comparator_class

    def _differs(self):
        return self.get_related_comparator().compare_fields()

    def get_related_comparator(self):
        if self.internal_comparator is None:
            self.internal_comparator = self.related_comparator_class(self.first, self.second)
        return self.internal_comparator

    @Decorators.init_differ
    def differ_fields(self):
        return self.get_related_comparator().compare_fields()


class OneToOneCompareField(InternalFieldComparator):
    pass


class FieldAsComparator(InternalFieldComparator):
    widget = MultipleCompareWidget()
    internal_comparator_instances = None

    def __iter__(self):
        for comparator in self.internal_comparator_instances:
            yield comparator

    def _differs(self):
        self.internal_comparator_instances = []
        diffs = 0
        for i in range(max([self.first.count(), self.second.count()])):
            first = self.first[i] if i < len(self.first) else None
            second = self.second[i] if i < len(self.second) else None
            comparator = self.related_comparator_class(first, second)
            self.internal_comparator_instances.append(comparator)

            diffs += comparator.compare()
        return diffs

    @Decorators.init_differ
    def differ_fields(self):
        self.internal_comparator_instances = []
        changed_fields = []
        for i in range(max([self.first.count(), self.second.count()])):
            first = self.first[i] if i < len(self.first) else None
            second = self.second[i] if i < len(self.second) else None
            comparator = self.related_comparator_class(first, second)
            self.internal_comparator_instances.append(comparator)

            changed_fields.extend(comparator.compare_fields())
        return changed_fields

    def get_related_comparator(self):
        return self


class RelatedForeignKeyCompareField(FieldAsComparator):
    pass


def compare_field_factory(field, related_comparator=None):
    if isinstance(field, models.CharField):
        return CompareField(field.name, field.verbose_name)

    if isinstance(field, models.OneToOneRel):
        return OneToOneCompareField(field.name, field.related_model._meta.verbose_name, related_comparator)

    if isinstance(field, models.ManyToOneRel):
        return RelatedForeignKeyCompareField(field.name, field.related_model._meta.verbose_name, related_comparator)

    return CompareField(field.name, field.verbose_name)
