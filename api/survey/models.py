from django.db.models import CASCADE


def NON_POLYMORPHIC_CASCADE(collector, field, sub_objs, using):
    """
    Специально для полиморфиков.
    """
    return CASCADE(collector, field, sub_objs.non_polymorphic(), using)
