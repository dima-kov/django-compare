from django.forms.renderers import TemplatesSetting
from django.utils.safestring import mark_safe


class BaseCompareWidget:
    template_name = 'comparison/widgets/compare_field.html'
    renderer = TemplatesSetting()

    def render(self, first, second, differ, field_label):
        context = self.get_context_data(first, second, differ, field_label)
        return mark_safe(self.renderer.render(self.template_name, context))

    @staticmethod
    def get_context_data(first, second, differences, field_label):
        return {
            'first': first,
            'second': second,
            'differences': differences,
            'field_label': field_label,
        }


class CompareWidget(BaseCompareWidget):
    pass


class InternalCompareWidget(BaseCompareWidget):
    template_name = 'comparison/widgets/multiple_compare_field.html'

    def render(self, internal_comparator, differences, field_label):
        related_result = ''
        for field in internal_comparator:
            related_result += field.render()

        context = self.get_context_data(related_result, differences, field_label)
        return mark_safe(self.renderer.render(self.template_name, context))

    @staticmethod
    def get_context_data(related_result, differences, field_label):
        return {
            'related_result': related_result,
            'differences': differences,
            'field_label': field_label,
        }


class MultipleCompareWidget(BaseCompareWidget):
    template_name = 'comparison/widgets/multiple_compare_field.html'

    def render(self, internal_comparator, differences, field_label):
        related_result = ''
        for comparator in internal_comparator:
            for field in comparator:
                related_result += field.render()

        context = self.get_context_data(related_result, differences, field_label)
        return mark_safe(self.renderer.render(self.template_name, context))

    @staticmethod
    def get_context_data(related_result, differences, field_label):
        return {
            'related_result': related_result,
            'differences': differences,
            'field_label': field_label,
        }
