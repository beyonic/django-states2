
from django.db.models.fields.related import ForeignKey

class StateField(ForeignKey):
    """
    Statefield for a model.
    Actually a ForeignKey, but this field also makes sure that the initial
    state is automatically created after initiation of the model.
    """
    def __init__(self, machine):
        ForeignKey.__init__(self, machine, null=False, blank=False, unique=True)
        self.__machine_state = machine

    def contribute_to_class(self, cls, name):
        self.__name = name
        models.signals.class_prepared.connect(self.__finalize, sender=cls)

        # Call contribute_to_class of parent
        ForeignKey.contribute_to_class(self, cls, name)

    def __finalize(self, sender, **kwargs):
        # Create field descriptor in model
        descriptor = getattr(sender, self.name, descriptor)
        self.__capture_set_method(descriptor)

        # Capture save method
        self.__capture_save_method(sender)

    def __capture_set_method(self, descriptor):
        """
        A state should never be assigned by hand.
        """
        raise AttributeError("You shouldn't set the state this way.")

    def __capture_save_method(self, sender):
        """
        The state is created during the first save.
        """
        original_save = sender.save

        @wraps(original_save)
        def new_save(instance, *args, **kwargs):
            # If no state has been defined for this instance, save a state first.
            if getattr(instance, self.__name) is None:
                state = self.__machine_state()
                state.save()
                setattr(instance, self.__name, state)

            # Call original save method
            original_save(instance, *args, **kwargs)

            # Save state
            pass

        sender.save = new_save
