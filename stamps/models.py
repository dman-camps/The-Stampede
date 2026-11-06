from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

# Create models here.
class Stamp(models.Model):
    CATEGORY_CHOICES = [
        ('study', 'Study'),
        ('social', 'Social'),
        ('sports', 'Sports'),
        ('volunteering', 'Volunteering'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    title = models.CharField(max_length=100) #max length tbd?
    desc = models.TextField()
    date = models.DateField() #separate date/time instead of DateTimeField() for easier editing
    time = models.TimeField()  # Event start time
    end_time = models.TimeField(null=True, blank=True)  # Event end time
    location = models.CharField(max_length=255) #could also be URLField(). for google maps link (?)
    cost = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    max_participants = models.PositiveIntegerField( validators=[MinValueValidator(2)] ) #number of max possible participants, set by organizer of event
    num_participants = models.PositiveIntegerField(default=0) #number of confirmed participants

    #TODO: remove null=True and blank=True once all stamps require a creator. its like this temporarily because it will give an error if a stamp is created without a creator
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) #stores which student created the stamp

    #checks cost and participant limit
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(cost__gte=0),
                name="stamp_cost_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(max_participants__gte=2),
                name="stamp_max_participants_min_2",
            ),
        ]

    def __str__(self):
        return self.title
    
#links a student to a stamp they have joined
class StampParticipation(models.Model): 
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stamp = models.ForeignKey(Stamp, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True) #records when the student joined

#prevents students from joining the same stamp more than once
    class Meta:
        unique_together = ('user', 'stamp')

    def __str__(self):
        return f"{self.user.username} - {self.stamp.title}"

#records which student reported a stamp, which stamp was reported, and why
class Report(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    stamp = models.ForeignKey(Stamp, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"Report by {self.reporter.username} for {self.stamp.title}"
