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
    type = models.CharField(max_length=6, choices=[('system', 'System'), ('user', 'User')], default='system')
    text_color = models.CharField(max_length=10, blank=True)
    background_color = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return "<Label %s (%s)>" % (self.name, self.google_id)


class Email(models.Model):
    """
    Basic Email model.
    """
    # Relations
    user = models.ForeignKey(User, related_name='emails', on_delete=models.CASCADE)

    # Many to Many relations
    labels = models.ManyToManyField(Label, related_name='emails')

    # Soft relations
    google_id = models.CharField(max_length=16)
    thread_id = models.CharField(max_length=16)

    # Attributes
    subject = models.TextField()
    snippet = models.TextField()
    sender = models.CharField(max_length=254)
    receiver = models.CharField(max_length=254)
    delivered_to = models.CharField(max_length=254)
    starred = models.BooleanField(default=False)
    important = models.BooleanField(default=False)
    date = models.DateTimeField()
    list_unsubscribe = models.TextField(blank=True)

    class Meta:
        unique_together = ['google_id', 'thread_id']

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
                                   starred=obj.get('starred', False),
                                   important=obj.get('important', False),
                                   date=obj['date'],
                                   list_unsubscribe=obj.get('list_unsubscribe', ''))
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


class LockedEmail(models.Model):
    """
    Basic model to contain email id and locked status.
    """
    # Relations
    user = models.ForeignKey(User, related_name='locked_emails', on_delete=models.CASCADE)

    # Soft relations
    google_id = models.CharField(max_length=16)
    thread_id = models.CharField(max_length=16)

    # Attributes
    locked = models.BooleanField(default=False)

    def __str__(self):
        return "<Locked Email %s: %s>" % (self.google_id, self.locked)
