# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Counter(models.Model):
    bucket = models.IntegerField(unique=True)
    count = models.IntegerField(default=0)
