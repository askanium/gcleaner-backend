from django.db import models

from gcleaner.users.models import User


class Label(models.Model):
    """
    Basic Label model.
    """
    # Relations
    user = models.ForeignKey(User, related_name='labels', on_delete=models.CASCADE)

    # Soft relations
    google_id = models.CharField(max_length=255)

    # Attributes
    name = models.CharField(max_length=255)

    def __repr__(self):
        return "<Label %s>" % self.name


class Email(models.Model):
    """
    Basic Email model.
    """
    # Relations
    user = models.ForeignKey(User, related_name='emails', on_delete=models.CASCADE)

    # Many to Many relations
    labels = models.ManyToManyField(Label, related_name='emails')

    # Soft relations
    google_id = models.CharField(max_length=16, unique=True)
    thread_id = models.CharField(max_length=16, unique=True)

    # Attributes
    subject = models.TextField()
    snippet = models.TextField()
    sender = models.CharField(max_length=254)
    receiver = models.CharField(max_length=254)
    delivered_to = models.CharField(max_length=254)
    starred = models.BooleanField(default=False)
    important = models.BooleanField(default=False)
    date = models.DateTimeField()

    def __str__(self):
        return "<Email %s>" % self.google_id

    @classmethod
    def from_dict(cls, obj):
        """
        Creates an instance of Email from a dict.
        :param {dict} obj: The object based on which to create an Email instance.
        :return: The newly created `gcleaner.emails.Email` instance.
        """
        email = cls.objects.create(user_id=obj['user'],
                                   google_id=obj['google_id'],
                                   thread_id=obj['thread_id'],
                                   subject=obj['subject'],
                                   snippet=obj['snippet'],
                                   sender=obj['sender'],
                                   receiver=obj['receiver'],
                                   delivered_to=obj['delivered_to'],
                                   starred=obj['starred'],
                                   important=obj['important'],
                                   date=obj['date'])
        for label_id in obj['labels']:
            label = Label.objects.get(user_id=obj['user'], google_id=label_id)
            email.labels.add(label)

        return email


class LatestEmail(models.Model):
    """
    Contains info related to the latest email of a User.
    """
    # Relations
    user = models.OneToOneField(User, related_name='latest_email', on_delete=models.CASCADE)
    email = models.OneToOneField(Email, related_name='latest_email', on_delete=models.CASCADE)

    def __str__(self):
        return "<LatestEmail %s>" % self.email
