from django.dispatch import Signal

# activity creation signal
activity = Signal(providing_args=['verb', 'object', 'target',
                                  'created_at'])
