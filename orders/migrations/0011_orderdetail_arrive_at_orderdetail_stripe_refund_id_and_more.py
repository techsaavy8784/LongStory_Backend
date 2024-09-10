# Generated by Django 4.2.5 on 2023-11-07 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_payment_bank_name_payment_brand_payment_country_and_more'),
        ('orders', '0010_orderdetail_amount_paid_orderdetail_payment_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='arrive_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='stripe_refund_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='billing_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='order_billing_addresses', to='users.address'),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='payment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='orders', to='users.payment'),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='shipping_address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='order_shipping_addresses', to='users.address'),
        ),
    ]
