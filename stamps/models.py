from django.db import models

# Create your models here.
class Stamp(models.Model):
    title = models.CharField(max_length=100) #max length tbd?
    desc = models.TextField()
    date = models.DateField() #separate date/time instead of DateTimeField() for easier editing
    time = models.TimeField()
    location = models.CharField(max_length=255) #could also be URLField(). for google maps link (?)
    cost = models.DecimalField( #assume $USD because this is exclusive to UNO
        max_digits=8,
        decimal_places=2,
        default=0
    )
    max_participants = models.PositiveIntegerField() #number of max possible participants, set by organizer of event
    num_participants = models.PositiveIntegerField(default=0) #number of confirmed participants

    def __str__(self):
        return self.title