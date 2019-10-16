from collections import OrderedDict
from itertools import chain

from django.core.exceptions import FieldError, ImproperlyConfigured
from django.db.models import OneToOneRel, ManyToOneRel, ForeignKey
from django.forms import ALL_FIELDS
from django.forms.forms import DeclarativeFieldsMetaclass

from compare.fields import compare_field_factory


class ModelComparatorOptions:
    def __init__(self, options=None):
        self.model = getattr(options, 'model', None)
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)
        self.related = getattr(options, 'related', None)
        self.widgets = getattr(options, 'widgets', None)


class ModelComparatorMetaclass(DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super(ModelComparatorMetaclass, mcs).__new__(mcs, name, bases, attrs)

        opts = new_class._meta = ModelComparatorOptions(getattr(new_class, 'Meta', None))

        # We check if a string was passed to `fields` or `exclude`,
        # which is likely to be a mistake where the user typed ('foo') instead
        # of ('foo',)
        for opt in ['fields', 'exclude']:
            value = getattr(opts, opt)
            if isinstance(value, str) and value != ALL_FIELDS:
                msg = ("%(model)s.Meta.%(opt)s cannot be a string. "
                       "Did you mean to type: ('%(value)s',)?" % {
                           'model': new_class.__name__,
                           'opt': opt,
                           'value': value,
                       })
                raise TypeError(msg)

        if opts.model:
            # If a model is defined, extract form fields from it.
            if opts.fields is None and opts.exclude is None:
                raise ImproperlyConfigured(
                    "Creating a ModelComparator without either the 'fields' attribute "
                    "or the 'exclude' attribute is prohibited; comparator %s "
                    "needs updating." % name
                )

            if opts.fields == ALL_FIELDS:
                # Sentinel for fields_for_model to indicate "get the list of
                # fields from the model"
                opts.fields = None

            fields = fields_for_comparator(
                opts.model, opts.fields, opts.exclude, opts.related, opts.widgets,
            )

            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = {k for k, v in fields.items() if not v}
            missing_fields = none_model_fields.difference(new_class.declared_fields)
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise FieldError(message)
        else:
            fields = new_class.declared_fields

        new_class.base_fields = fields

        return new_class


def fields_for_comparator(model, fields=None, exclude=None, related_comparators=None, widgets=None):
    """
    Return an ``OrderedDict`` containing form fields for the given model.

    ``fields`` is an optional list of field names. If provided, return only the
    named fields.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named fields from the returned fields, even if they are listed in the
    ``fields`` argument.
    """
    field_list = []
    ignored = []
    opts = model._meta
    # Avoid circular import
    from django.db.models.fields import Field as ModelField
    sortable_private_fields = [f for f in opts.private_fields if isinstance(f, ModelField)]
    for f in chain(opts.concrete_fields, sortable_private_fields, opts.many_to_many, opts.related_objects):
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue

        kwargs = {}
        if related_comparators:
            kwargs['related_comparator'] = related_comparators.get(f.name, None)
        if widgets:
            kwargs['widget'] = widgets.get(f.name, None)

        compare_field = compare_field_factory(f, **kwargs)

        if compare_field:
            field_list.append((f.name, compare_field))
        else:
            ignored.append(f.name)

    field_dict = OrderedDict(field_list)
    if fields:
        field_dict = OrderedDict(
            [(f, field_dict.get(f)) for f in fields
             if ((not exclude) or (exclude and f not in exclude)) and (f not in ignored)]
        )
    return field_dict


def model_to_dict(instance, fields=None, exclude=None):
    """
    Equivalent to django.forms.models.model_to_dict
    Return a dict containing the data in ``instance``

    ``fields`` is an optional list of field names. If provided, return only the
    named.

    ``exclude`` is an optional list of field names. If provided, exclude the
    named from the returned dict, even if they are listed in the ``fields``
    argument.
    """
    if instance is None:
        return {}
    opts = instance._meta
    data = {}
    for f in opts.get_fields():
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue

        if isinstance(f, OneToOneRel):
            data[f.name] = getattr(instance, f.name)
        elif isinstance(f, ManyToOneRel):
            data[f.name] = getattr(instance, f.name).all()
        elif isinstance(f, ForeignKey):
            data[f.name] = getattr(instance, f.name)
        else:
            data[f.name] = f.value_from_object(instance)

    return data
