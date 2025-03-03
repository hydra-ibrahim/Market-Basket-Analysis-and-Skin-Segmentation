from django.db import models

# Create your models here.
class Item(models.Model):
    name = models.CharField(primary_key=True, max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'items'

    def __str__(self) -> str:
        return self.name