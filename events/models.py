import datetime
import os
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class BaseModel(models.Model):
    record_created = models.DateTimeField(editable=False, auto_now_add=True)
    record_modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """ On save, update timestamps """
        if not self.id:
            self.record_created = timezone.now()
        self.record_modified = timezone.now()
        return super(BaseModel, self).save(*args, **kwargs)


class Club(BaseModel):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class EventCategory(BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False)
    coverImage = models.ImageField(upload_to='images/eventCategory/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Event Categories"

    def __str__(self):
        return self.name


class EventType(BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False)
    eventCategory = models.ForeignKey(EventCategory, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='event_types')
    coverImage = models.ImageField(upload_to='images/eventType/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Event Types"

    def __str__(self):
        return self.name


class Event(BaseModel):
    # Primary Info
    name = models.CharField(max_length=256)
    coordinators = models.ManyToManyField(to=User)

    # Venue and Date
    locations = models.CharField(max_length=256)
    dateTime = models.DateTimeField(verbose_name="Date and Time of Event", default=datetime.datetime.now)

    # Prize Details
    prize = models.TextField(blank=True)

    # Team Member
    minTeam = models.IntegerField(verbose_name="Minimum Size of the Team", validators=[MinValueValidator(0)], default=0)
    maxTeam = models.IntegerField(verbose_name="Maximum Size of the Team", validators=[MinValueValidator(0)], default=0)

    # Detailed Info
    eventType = models.ForeignKey(EventType, verbose_name="Type of the event",
                                  on_delete=models.SET_NULL, null=True, related_name='events')

    association = models.ForeignKey(Club, verbose_name="Name of the club/society associated with this event",
                                    on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    details = models.TextField(blank=True)
    shortDescription = models.TextField(blank=True, verbose_name="Short Description about event")
    ruleList = models.TextField(blank=True, verbose_name="List of the rules")

    # Files attached
    poster = models.ImageField(upload_to='images/events/', null=True, blank=True)
    rulesPDF = models.FileField(upload_to='pdf/events/', null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Registration(BaseModel):
    registered_event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')

    def __str__(self):
        return self.registered_event.name + " - " + self.participant.username

    class Meta:
        permissions = (
            ('allowed_import', "Imports are allowed"),
        )


class Sponsor(BaseModel):
    name = models.CharField(max_length=256, null=False)
    tagline = models.CharField(max_length=512, blank=True, null=True)
    partnership = models.CharField(max_length=256, blank=True, null=True)
    logo = models.ImageField(upload_to='Images/sponsors/', null=True, blank=True)

    def __str__(self):
        return self.name


class Brochure(BaseModel):
    name = models.CharField(max_length=256, null=False, blank=False)
    brochurePDF = models.FileField(upload_to='pdf/brochure/', null=True, blank=True)

    def __str__(self):
        return self.name


def path_and_rename(instance, filename):
    upload_to = 'PanCard'
    ext = filename.split('.')[-1]
    # get filename
    if instance.pk:
        filename = '{}.{}'.format(instance.user.username, ext)
    else:
        # set filename as random string
        filename = '{}.{}'.format(uuid4().hex, ext)
    # return the whole path to the file
    return os.path.join(upload_to, filename)


class DetailWinner(BaseModel):

    user = models.OneToOneField(to=User, null=False, related_name='account_details', on_delete=models.CASCADE)
    accountHolderName = models.CharField(max_length=100, null=False, blank=False)
    fatherName = models.CharField(max_length=100, null=False, blank=False, )
    accountNumber = models.CharField(max_length=20, null=False)
    IFSC = models.CharField(max_length=25)
    panCardNumber = models.CharField(max_length=11, blank=True, null=False)
    panCardPhoto = models.ImageField(upload_to=path_and_rename, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Details of Individual Winner of each team"

    def __str__(self):
        return self.accountHolderName


class TeamWinner(BaseModel):

    TeamName = models.CharField(max_length=100, null=False, blank=False, help_text="In case of Individual "
                                                                                   "Participant, Add "
                                                                                   "ParticipantName_EventName into "
                                                                                   "this field for easy Reference")
    members = models.ManyToManyField(to=DetailWinner, help_text="Create new Model of Winner as per number of team "
                                                                "members AND check for existing entry first!")

    class Meta:
        verbose_name_plural = "Team of Winner(s)"

    def __str__(self):
        return self.TeamName


class Winners(BaseModel):

    eventName = models.OneToOneField(to=Event, null=False, blank=False, on_delete=models.PROTECT)
    firstWinner = models.OneToOneField(to=TeamWinner, on_delete=models.PROTECT, help_text="Add new team by clicking + "
                                                                                          "button",
                                       related_name="firstWinner")
    secondWinner = models.OneToOneField(to=TeamWinner, on_delete=models.PROTECT, null=True, blank=True,
                                        related_name="secondWinner")
    thirdWinner = models.OneToOneField(to=TeamWinner, on_delete=models.PROTECT, null=True, blank=True,
                                       related_name="thirdWinner")

    class Meta:
        verbose_name_plural = "Winners"

    def __str__(self):
        return self.eventName.name
